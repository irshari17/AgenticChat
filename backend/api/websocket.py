"""
WebSocket endpoint for streaming chat.
"""

import json
import asyncio
import uuid
from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from graph.graph_builder import get_compiled_graph
from core.dependencies import get_session_manager
from schemas.messages import MessageType

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str = None):
    """
    WebSocket endpoint for streaming chat.
    
    Client sends: {"message": "user text"}
    Server streams: {"type": "...", "content": "..."}
    """
    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())

    await manager.connect(websocket, session_id)

    # Send session info
    await websocket.send_json({
        "type": MessageType.STATUS.value,
        "content": f"Connected to session: {session_id}",
        "session_id": session_id,
    })

    try:
        while True:
            # Wait for user message
            data = await websocket.receive_text()
            
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                msg = {"message": data}

            user_message = msg.get("message", "")
            if not user_message:
                continue

            # Create streaming callback
            async def stream_callback(event: Dict[str, Any]):
                """Callback to stream events to the WebSocket client."""
                await websocket.send_json({
                    "type": event.get("type", "status"),
                    "content": event.get("content", ""),
                    "session_id": session_id,
                })

            # Build initial state
            session_manager = get_session_manager()
            session = session_manager.get_or_create(session_id)

            initial_state = {
                "user_query": user_message,
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
                "stream_callback": stream_callback,
            }

            try:
                # Run the graph
                graph = get_compiled_graph()
                result = await graph.ainvoke(initial_state)

                # Send final complete message
                await websocket.send_json({
                    "type": MessageType.ASSISTANT_MESSAGE.value,
                    "content": result.get("final_response", ""),
                    "session_id": session_id,
                    "metadata": {
                        "plan": result.get("plan"),
                        "task_results": result.get("task_results", []),
                    },
                })

            except Exception as e:
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "content": f"Error processing request: {str(e)}",
                    "session_id": session_id,
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        manager.disconnect(session_id)
