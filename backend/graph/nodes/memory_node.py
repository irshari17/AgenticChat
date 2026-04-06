"""
Memory Node: LangGraph node for storing and retrieving memory.
"""

from typing import Dict, Any
from graph.state import AgentState
from memory.memory_store import MemoryStore
from memory.session_memory import SessionMemoryManager
from schemas.messages import MessageRole
from core.dependencies import get_memory_store, get_session_manager
from services.llm import LLMService
from core.dependencies import get_llm_service


async def memory_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node that updates memory and generates the final response.
    Stores the interaction and synthesizes results into a coherent response.
    """
    memory_store = get_memory_store()
    session_manager = get_session_manager()
    llm = get_llm_service()

    session_id = state.get("session_id", "default")
    session = session_manager.get_or_create(session_id)
    callback = state.get("stream_callback")

    # Collect results
    user_query = state.get("user_query", "")
    task_results = state.get("task_results", [])
    direct_response = state.get("direct_response")
    plan = state.get("plan")

    # Store the user message in session
    session.add_message(MessageRole.USER, user_query)

    # Store in memory store for retrieval
    memory_store.add(
        content=f"User asked: {user_query}",
        metadata={"type": "user_query", "session_id": session_id},
    )

    # Generate final response
    if direct_response:
        # Planner decided no tools needed — generate conversational response
        final_response = await _generate_conversational_response(
            llm, user_query, session.get_context_string(last_n=10)
        )
    elif task_results:
        # Synthesize results from tool executions
        final_response = await _synthesize_results(
            llm, user_query, task_results, session.get_context_string(last_n=5)
        )
    else:
        final_response = await _generate_conversational_response(
            llm, user_query, session.get_context_string(last_n=10)
        )

    # Store assistant response in session and memory
    session.add_message(MessageRole.ASSISTANT, final_response)
    memory_store.add(
        content=f"Assistant responded: {final_response[:500]}",
        metadata={"type": "assistant_response", "session_id": session_id},
    )

    # Stream the final response
    if callback:
        await callback({
            "type": "stream_start",
            "content": "",
        })
        # Stream the response in chunks
        chunk_size = 10  # characters per chunk for visual effect
        for i in range(0, len(final_response), chunk_size):
            chunk = final_response[i:i + chunk_size]
            await callback({
                "type": "assistant_chunk",
                "content": chunk,
            })
        await callback({
            "type": "stream_end",
            "content": "",
        })

    return {
        "final_response": final_response,
    }


async def _generate_conversational_response(llm: LLMService, query: str, context: str) -> str:
    """Generate a conversational response using the LLM."""
    system_prompt = (
        "You are a helpful, knowledgeable AI assistant. "
        "Respond naturally and conversationally. "
        "Be concise but thorough."
    )

    messages = []
    if context:
        messages.append({"role": "system", "content": f"Previous conversation:\n{context}"})
    messages.append({"role": "user", "content": query})

    return await llm.complete(messages=messages, system_prompt=system_prompt)


async def _synthesize_results(
    llm: LLMService,
    query: str,
    task_results: list,
    context: str,
) -> str:
    """Synthesize task results into a coherent response."""
    results_text = "\n\n".join([
        f"Step {r.get('step_index', 0) + 1} ({r.get('type', 'unknown')}"
        f"{' - ' + r.get('tool_name', '') if r.get('tool_name') else ''}):\n"
        f"Result: {r.get('result', 'No result')}"
        for r in task_results
    ])

    system_prompt = (
        "You are a helpful AI assistant. The user made a request, and tools were used to gather information. "
        "Synthesize the tool results into a clear, helpful, and well-formatted response for the user. "
        "Do not mention the internal tools or execution steps unless relevant."
    )

    messages = [
        {"role": "user", "content": f"User's original request: {query}\n\nTool execution results:\n{results_text}"}
    ]

    return await llm.complete(messages=messages, system_prompt=system_prompt)
