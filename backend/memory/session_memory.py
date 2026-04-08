"""
Per-session chat history management.
"""

from typing import Dict, List, Optional
from datetime import datetime
from schemas.messages import ChatMessage, MessageRole
import uuid
import logging

logger = logging.getLogger("memory.session")


class SessionMemory:
    def __init__(self, session_id: str, max_history: int = 50):
        self.session_id = session_id
        self.max_history = max_history
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.utcnow()
        self.metadata: Dict = {}

    def add_message(self, role: MessageRole, content: str, metadata: Dict = None) -> ChatMessage:
        msg = ChatMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)

        if len(self.messages) > self.max_history:
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]
            keep = self.max_history - len(system_msgs)
            self.messages = system_msgs + other_msgs[-keep:]

        return msg

    def get_history(self, last_n: Optional[int] = None) -> List[ChatMessage]:
        return self.messages[-last_n:] if last_n else self.messages

    def get_context_string(self, last_n: int = 10) -> str:
        history = self.get_history(last_n=last_n)
        return "\n".join(f"{m.role.value.capitalize()}: {m.content}" for m in history)

    def clear(self):
        self.messages.clear()


class SessionMemoryManager:
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.sessions: Dict[str, SessionMemory] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> SessionMemory:
        if not session_id:
            session_id = str(uuid.uuid4())
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(session_id, self.max_history)
            logger.info(f"Session created: {session_id}")
        return self.sessions[session_id]

    def get(self, session_id: str) -> Optional[SessionMemory]:
        return self.sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        return list(self.sessions.keys())
