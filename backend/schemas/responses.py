"""
Pydantic schemas for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ChatResponse(BaseModel):
    session_id: str
    message: str
    plan: Optional[Dict[str, Any]] = None
    tool_results: List[Dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionResponse(BaseModel):
    session_id: str
    message_count: int
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: int = 500
