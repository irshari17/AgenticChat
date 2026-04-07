"""
REST API routes.
"""

import uuid
from fastapi import APIRouter, HTTPException
from schemas.messages import UserInput
from core.dependencies import get_session_manager, get_tool_executor
from graph.graph_builder import get_compiled_graph

router = APIRouter()


@router.post("/chat")
async def chat(input: UserInput):
    """Non-streaming chat endpoint."""
    session_manager = get_session_manager()
    session_id = input.session_id or str(uuid.uuid4())
    session = session_manager.get_or_create(session_id)

    initial_state = {
        "user_query": input.message,
        "session_id": session_id,
        "context": session.get_context_string(last_n=10),
        "chat_history": [],
        "plan": None,
        "current_step_index": 0,
        "needs_execution": False,
        "tasks": [],
        "current_task": None,
        "task_results": [],
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "final_response": "",
        "response_chunks": [],
        "should_continue": False,
        "error": None,
        "direct_response": None,
        "stream_callback": None,
    }

    try:
        graph = get_compiled_graph()
        result = await graph.ainvoke(initial_state)
        return {
            "session_id": session_id,
            "message": result.get("final_response", "Could not generate response."),
            "plan": result.get("plan"),
            "task_results": result.get("task_results", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    session_manager = get_session_manager()
    sessions = []
    for sid in session_manager.list_sessions():
        session = session_manager.get(sid)
        if session:
            sessions.append({
                "session_id": sid,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
            })
    return {"sessions": sessions}


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    session_manager = get_session_manager()
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "messages": [
            {"id": m.id, "role": m.role.value, "content": m.content, "timestamp": m.timestamp.isoformat()}
            for m in session.get_history()
        ],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    session_manager = get_session_manager()
    if session_manager.delete(session_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/tools")
async def list_tools():
    executor = get_tool_executor()
    return {"tools": executor.get_tool_schemas()}
