"""
Session-based chat history management.
Tracks per-session conversation history and context.
"""

from typing import Dict, List, Optional
from datetime import datetime
from schemas.messages import ChatMessage, MessageRole
import uuid


class SessionMemory:
    """Chat history for a single session."""

    def __init__(self, session_id: str, max_history: int = 50):
        self.session_id = session_id
        self.max_history = max_history
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.utcnow()
        self.metadata: Dict = {}

    def add_message(self, role: MessageRole, content: str, metadata: Dict = None) -> ChatMessage:
        """Add a message to the session history."""
        msg = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(msg)

        # Trim to max history (keep system messages)
        if len(self.messages) > self.max_history:
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]
            other_msgs = other_msgs[-(self.max_history - len(system_msgs)):]
            self.messages = system_msgs + other_msgs

        return msg

    def get_history(self, last_n: Optional[int] = None) -> List[ChatMessage]:
        """Get chat history, optionally limited to last N messages."""
        if last_n is not None:
            return self.messages[-last_n:]
        return self.messages

    def get_context_string(self, last_n: int = 10) -> str:
        """Get formatted chat history as a context string for LLM."""
        history = self.get_history(last_n=last_n)
        lines = []
        for msg in history:
            role_label = msg.role.value.capitalize()
            lines.append(f"{role_label}: {msg.content}")
        return "\n".join(lines)

    def clear(self):
        """Clear all messages."""
        self.messages.clear()


class SessionMemoryManager:
    """Manages multiple session memories."""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.sessions: Dict[str, SessionMemory] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> SessionMemory:
        """Get existing session or create a new one."""
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(
                session_id=session_id,
                max_history=self.max_history,
            )

        return self.sessions[session_id]

    def get(self, session_id: str) -> Optional[SessionMemory]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self.sessions.keys())
