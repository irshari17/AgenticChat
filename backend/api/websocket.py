"""
WebSocket endpoint for streaming chat.
All agent activity, tool calls, and responses are streamed in real-time.
"""

import json
import uuid
import traceback
from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from graph.graph_builder import get_compiled_graph
from core.dependencies import get_session_manager
from schemas.messages import MessageType
import logging

logger = logging.getLogger("api.websocket")
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        self.connections[session_id] = ws

    def disconnect(self, session_id: str):
        self.connections.pop(session_id, None)

    async def send(self, session_id: str, data: Dict[str, Any]):
        ws = self.connections.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str = "new"):
    """Main WebSocket endpoint for streaming agent chat."""

    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())

    await manager.connect(websocket, session_id)
    logger.info(f"WS connected: {session_id[:12]}...")

    # Send session confirmation
    try:
        await websocket.send_json({
            "type": MessageType.STATUS.value,
            "content": f"Connected to session: {session_id}",
            "session_id": session_id,
        })
    except Exception as e:
        logger.error(f"Failed to send initial message: {e}")
        manager.disconnect(session_id)
        return

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                msg = {"message": raw}

            user_message = msg.get("message", "").strip()
            if not user_message:
                continue

            logger.info(f"[{session_id[:8]}] {user_message[:100]}...")

            # Build callback that captures current websocket and session_id
            _ws = websocket
            _sid = session_id

            async def stream_callback(event: Dict[str, Any]):
                try:
                    await _ws.send_json({
                        "type": event.get("type", "status"),
                        "content": event.get("content", ""),
                        "session_id": _sid,
                    })
                except Exception as cb_err:
                    logger.warning(f"Stream callback error: {cb_err}")

            # Build state
            session_manager = get_session_manager()
            session = session_manager.get_or_create(session_id)

            initial_state = {
                "user_query": user_message,
                "session_id": session_id,
                "context": session.get_context_string(last_n=10),
                "chat_history": [],
                "classification": "",
                "needs_planning": False,
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
                graph = get_compiled_graph()
                result = await graph.ainvoke(initial_state)

                # Send final complete message
                await websocket.send_json({
                    "type": MessageType.ASSISTANT_MESSAGE.value,
                    "content": result.get("final_response", ""),
                    "session_id": session_id,
                    "metadata": {
                        "classification": result.get("classification"),
                        "task_results": [
                            {k: v for k, v in r.items() if k != "result" or len(str(v)) < 500}
                            for r in result.get("task_results", [])
                        ],
                    },
                })

                logger.info(f"[{session_id[:8]}] Response sent")

            except Exception as e:
                error_msg = f"Processing error: {str(e)}"
                logger.error(f"[{session_id[:8]}] {error_msg}")
                traceback.print_exc()
                try:
                    await websocket.send_json({
                        "type": MessageType.ERROR.value,
                        "content": error_msg,
                        "session_id": session_id,
                    })
                except Exception:
                    pass

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {session_id[:12]}")
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WS error: {e}")
        traceback.print_exc()
        manager.disconnect(session_id)
