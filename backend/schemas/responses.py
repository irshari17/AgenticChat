"""
Pydantic schemas for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from datetime import datetime


class ChatResponse(BaseModel):
    """Response for a chat interaction."""
    session_id: str
    message: str
    plan: Optional[Dict[str, Any]] = None
    tool_results: List[Dict[str, Any]] = []
    timestamp: datetime = datetime.utcnow()


class SessionResponse(BaseModel):
    """Response containing session information."""
    session_id: str
    message_count: int
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: int = 500
