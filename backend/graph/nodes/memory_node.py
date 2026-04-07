"""
Memory Node: stores interaction and generates final response.
"""

import asyncio
from typing import Dict, Any
from graph.state import AgentState
from schemas.messages import MessageRole
from core.dependencies import get_memory_store, get_session_manager, get_llm_service
from services.llm import LLMService


async def memory_node(state: AgentState) -> Dict[str, Any]:
    """Updates memory and generates the final response."""
    memory_store = get_memory_store()
    session_manager = get_session_manager()
    llm = get_llm_service()

    session_id = state.get("session_id", "default")
    session = session_manager.get_or_create(session_id)
    callback = state.get("stream_callback")

    user_query = state.get("user_query", "")
    task_results = state.get("task_results", [])
    direct_response = state.get("direct_response")

    # Store user message
    session.add_message(MessageRole.USER, user_query)
    memory_store.add(content=f"User asked: {user_query}", metadata={"type": "user_query"})

    # Generate response
    if direct_response:
        final_response = await _generate_conversational_response(
            llm, user_query, session.get_context_string(last_n=10)
        )
    elif task_results:
        final_response = await _synthesize_results(
            llm, user_query, task_results, session.get_context_string(last_n=5)
        )
    else:
        final_response = await _generate_conversational_response(
            llm, user_query, session.get_context_string(last_n=10)
        )

    # Store assistant response
    session.add_message(MessageRole.ASSISTANT, final_response)
    memory_store.add(content=f"Assistant: {final_response[:500]}", metadata={"type": "response"})

    # Stream final response
    if callback:
        await callback({"type": "stream_start", "content": ""})
        chunk_size = 15
        for i in range(0, len(final_response), chunk_size):
            chunk = final_response[i:i + chunk_size]
            await callback({"type": "assistant_chunk", "content": chunk})
            await asyncio.sleep(0.02)  # Small delay for visual streaming effect
        await callback({"type": "stream_end", "content": ""})

    return {"final_response": final_response}


async def _generate_conversational_response(llm: LLMService, query: str, context: str) -> str:
    system_prompt = (
        "You are a helpful AI assistant. Respond naturally and conversationally. Be concise but thorough."
    )
    messages = []
    if context:
        messages.append({"role": "system", "content": f"Previous conversation:\n{context}"})
    messages.append({"role": "user", "content": query})
    return await llm.complete(messages=messages, system_prompt=system_prompt)


async def _synthesize_results(llm: LLMService, query: str, task_results: list, context: str) -> str:
    results_text = "\n\n".join([
        f"Step {r.get('step_index', 0) + 1} ({r.get('type', 'unknown')}"
        f"{' - ' + r.get('tool_name', '') if r.get('tool_name') else ''}):\n"
        f"Result: {r.get('result', 'No result')}"
        for r in task_results
    ])
    system_prompt = (
        "You are a helpful AI assistant. Synthesize tool results into a clear response. "
        "Don't mention internal tools unless relevant."
    )
    messages = [
        {"role": "user", "content": f"Original request: {query}\n\nResults:\n{results_text}"}
    ]
    return await llm.complete(messages=messages, system_prompt=system_prompt)
