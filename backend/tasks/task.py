"""
Task representation with status tracking and logging.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "info"
    message: str


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "tool" or "agent"
    name: str = ""
    description: str = ""
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    depends_on: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    logs: List[TaskLog] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def start(self):
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.add_log("Task started")

    def complete(self, result: str):
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.add_log("Task completed")

    def fail(self, error: str):
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.add_log(f"Task failed: {error}", level="error")

    def cancel(self):
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.add_log("Task cancelled", level="warning")

    def retry(self):
        self.retry_count += 1
        self.status = TaskStatus.RETRYING
        self.error = None
        self.add_log(f"Retrying (attempt {self.retry_count})", level="warning")

    def add_log(self, message: str, level: str = "info"):
        self.logs.append(TaskLog(message=message, level=level))

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
