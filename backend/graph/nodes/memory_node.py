"""
Memory Node — stores interaction data and generates the final synthesized response.
"""

import asyncio
from typing import Dict, Any
from graph.state import AgentState
from schemas.messages import MessageRole
from core.dependencies import (
    get_memory_store, get_session_manager, get_llm_service,
    get_shared_memory, get_agent_registry,
)
from services.llm import LLMService
import logging

logger = logging.getLogger("graph.memory")


async def memory_node(state: AgentState) -> Dict[str, Any]:
    """Stores interaction in memory and generates the final response."""
    memory_store = get_memory_store()
    session_manager = get_session_manager()
    shared_memory = get_shared_memory()
    registry = get_agent_registry()
    llm = get_llm_service()

    session_id = state.get("session_id", "default")
    session = session_manager.get_or_create(session_id)
    callback = state.get("stream_callback")

    user_query = state.get("user_query", "")
    task_results = state.get("task_results", [])
    direct_response = state.get("direct_response")

    if callback:
        await callback({"type": "status", "content": "📝 Generating response..."})

    # Store user message
    session.add_message(MessageRole.USER, user_query)
    memory_store.add(content=f"User: {user_query}", category="conversation")

    # Generate final response
    if direct_response and not task_results:
        final_response = await _generate_direct_response(llm, user_query, session.get_context_string(last_n=10))
    elif task_results:
        # Add shared memory context
        shared_ctx = shared_memory.summary(session_id)
        final_response = await _synthesize_results(llm, user_query, task_results, shared_ctx)
    else:
        final_response = await _generate_direct_response(llm, user_query, session.get_context_string(last_n=10))

    # Store response
    session.add_message(MessageRole.ASSISTANT, final_response)
    memory_store.add(content=f"Assistant: {final_response[:500]}", category="conversation")

    # Store summary in shared memory
    shared_memory.set(
        key="last_response",
        value=final_response[:500],
        source_agent="memory_node",
        session_id=session_id,
    )

    # Stream final response to client
    if callback:
        await callback({"type": "stream_start", "content": ""})
        chunk_size = 12
        for i in range(0, len(final_response), chunk_size):
            chunk = final_response[i:i + chunk_size]
            await callback({"type": "assistant_chunk", "content": chunk})
            await asyncio.sleep(0.015)
        await callback({"type": "stream_end", "content": ""})

    # Log agent summary
    agent_summary = registry.summary()
    logger.info(f"Response generated ({len(final_response)} chars). Agents used: {agent_summary}")

    return {"final_response": final_response}


async def _generate_direct_response(llm: LLMService, query: str, context: str) -> str:
    system_prompt = (
        "You are a helpful, knowledgeable AI assistant. "
        "Respond naturally and conversationally. Be concise but thorough. "
        "Use markdown formatting when appropriate."
    )
    messages = []
    if context:
        messages.append({"role": "system", "content": f"Previous conversation:\n{context}"})
    messages.append({"role": "user", "content": query})
    return await llm.complete(messages=messages, system_prompt=system_prompt)


async def _synthesize_results(llm: LLMService, query: str, task_results: list, shared_ctx: str) -> str:
    results_text = "\n\n".join([
        f"Step {r.get('step_index', 0) + 1} ({r.get('type', 'unknown')}"
        f"{' — ' + r.get('tool_name', '') if r.get('tool_name') else ''}"
        f"{' — ' + r.get('task_description', '') if r.get('task_description') else ''}):\n"
        f"Result: {r.get('result', 'No result')}"
        for r in task_results
    ])

    system_prompt = (
        "You are a helpful AI assistant. The user made a request, and multiple steps were executed. "
        "Synthesize ALL the results into a clear, well-formatted, and helpful response. "
        "Use markdown formatting. Don't expose internal tool names unless the user asked about them. "
        "Be thorough but concise."
    )

    messages = [{
        "role": "user",
        "content": (
            f"Original request: {query}\n\n"
            f"Execution results:\n{results_text}\n\n"
            f"Additional context:\n{shared_ctx}"
        ),
    }]

    return await llm.complete(messages=messages, system_prompt=system_prompt)
