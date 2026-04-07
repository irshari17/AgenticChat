"""
WebSocket endpoint for streaming chat.
"""

import json
import uuid
import traceback
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

    async def send_json(self, session_id: str, message: Dict[str, Any]):
        ws = self.active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str = "new"):
    """WebSocket endpoint for streaming chat."""

    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())

    await manager.connect(websocket, session_id)
    print(f"✅ WebSocket connected: {session_id}")

    # Send session info
    try:
        await websocket.send_json({
            "type": MessageType.STATUS.value,
            "content": f"Connected to session: {session_id}",
            "session_id": session_id,
        })
    except Exception as e:
        print(f"Error sending initial message: {e}")
        manager.disconnect(session_id)
        return

    try:
        while True:
            # Wait for user message
            raw_data = await websocket.receive_text()

            try:
                msg = json.loads(raw_data)
            except json.JSONDecodeError:
                msg = {"message": raw_data}

            user_message = msg.get("message", "").strip()
            if not user_message:
                continue

            print(f"📨 Received: {user_message[:100]}...")

            # Create streaming callback — captures websocket and session_id
            async def make_callback(ws: WebSocket, sid: str):
                async def stream_callback(event: Dict[str, Any]):
                    try:
                        await ws.send_json({
                            "type": event.get("type", "status"),
                            "content": event.get("content", ""),
                            "session_id": sid,
                        })
                    except Exception as e:
                        print(f"Stream callback error: {e}")
                return stream_callback

            callback = await make_callback(websocket, session_id)

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
                "stream_callback": callback,
            }

            try:
                graph = get_compiled_graph()
                result = await graph.ainvoke(initial_state)

                # Send final message
                await websocket.send_json({
                    "type": MessageType.ASSISTANT_MESSAGE.value,
                    "content": result.get("final_response", ""),
                    "session_id": session_id,
                    "metadata": {
                        "task_results": result.get("task_results", []),
                    },
                })
                print(f"✅ Response sent for: {user_message[:50]}...")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(f"❌ Graph error: {error_msg}")
                traceback.print_exc()
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "content": error_msg,
                    "session_id": session_id,
                })

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {session_id}")
        manager.disconnect(session_id)
    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")
        traceback.print_exc()
        manager.disconnect(session_id)
