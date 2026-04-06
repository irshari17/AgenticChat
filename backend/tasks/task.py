"""
Task representation for the task system.
Each step in a plan is tracked as a Task with status, result, and logs.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskLog(BaseModel):
    """A single log entry for a task."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "info"
    message: str


class Task(BaseModel):
    """
    Represents a single executable task within a plan.
    Tracks execution status, results, and logs.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "tool" or "agent"
    name: str = ""
    description: str = ""
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    logs: List[TaskLog] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def start(self):
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.add_log("Task started")

    def complete(self, result: str):
        """Mark task as completed with a result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.add_log(f"Task completed: {result[:100]}...")

    def fail(self, error: str):
        """Mark task as failed with an error message."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.add_log(f"Task failed: {error}", level="error")

    def cancel(self):
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.add_log("Task cancelled", level="warning")

    def add_log(self, message: str, level: str = "info"):
        """Add a log entry."""
        self.logs.append(TaskLog(message=message, level=level))

    @property
    def is_terminal(self) -> bool:
        """Check if the task has reached a terminal state."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
