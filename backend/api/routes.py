"""
REST API routes for the chat system.
"""

from fastapi import APIRouter, HTTPException
from schemas.messages import UserInput
from schemas.responses import ChatResponse, SessionResponse, ErrorResponse
from core.dependencies import get_session_manager, get_memory_store
from graph.graph_builder import get_compiled_graph
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(input: UserInput):
    """
    Non-streaming chat endpoint.
    Processes the user's message through the full agent pipeline.
    """
    session_manager = get_session_manager()
    
    # Get or create session
    session_id = input.session_id or str(uuid.uuid4())
    session = session_manager.get_or_create(session_id)

    # Build initial state
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

        return ChatResponse(
            session_id=session_id,
            message=result.get("final_response", "I apologize, but I couldn't generate a response."),
            plan=result.get("plan"),
            tool_results=result.get("task_results", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    session_manager = get_session_manager()
    sessions = []
    for sid in session_manager.list_sessions():
        session = session_manager.get(sid)
        sessions.append({
            "session_id": sid,
            "message_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
        })
    return {"sessions": sessions}


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat history for a session."""
    session_manager = get_session_manager()
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in session.get_history()
        ],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    session_manager = get_session_manager()
    if session_manager.delete(session_id):
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/tools")
async def list_tools():
    """List all available tools."""
    from core.dependencies import get_tool_executor
    executor = get_tool_executor()
    return {
        "tools": executor.get_tool_schemas(),
    }
