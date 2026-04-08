"""
API response schemas.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatResponse(BaseModel):
    session_id: str
    message: str
    plan: Optional[Dict[str, Any]] = None
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    agents_used: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: int = 500
