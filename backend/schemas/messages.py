"""
Message schemas for the chat system.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    COORDINATOR = "coordinator"


class MessageType(str, Enum):
    USER_MESSAGE = "user_message"
    ASSISTANT_CHUNK = "assistant_chunk"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    PLAN = "plan"
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    COORDINATOR = "coordinator"
    ERROR = "error"
    STATUS = "status"
    STREAM_START = "stream_start"
    STREAM_END = "stream_end"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserInput(BaseModel):
    message: str
    session_id: Optional[str] = None
