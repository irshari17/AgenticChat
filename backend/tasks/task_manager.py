"""
Task Manager: creates, tracks, and manages tasks throughout execution.
"""

from typing import Dict, List, Optional
from tasks.task import Task, TaskStatus
from schemas.messages import ExecutionPlan, PlanStep
import uuid


class TaskManager:
    """
    Manages the lifecycle of tasks.
    Creates tasks from plans and tracks their execution.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.plan_tasks: Dict[str, List[str]] = {}  # plan_id -> [task_ids]

    def create_tasks_from_plan(self, plan: ExecutionPlan) -> List[Task]:
        """Create Task objects from an ExecutionPlan."""
        tasks = []
        task_ids = []

        for step in plan.steps:
            task = Task(
                type=step.type,
                name=step.tool or step.task or "unnamed",
                description=step.reasoning,
                tool_name=step.tool,
                tool_input=step.input or {},
                metadata={"plan_id": plan.plan_id, "step_id": step.step_id},
            )
            self.tasks[task.id] = task
            tasks.append(task)
            task_ids.append(task.id)

        self.plan_tasks[plan.plan_id] = task_ids
        return tasks

    def create_single_task(
        self,
        task_type: str,
        name: str,
        description: str = "",
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict] = None,
        parent_task_id: Optional[str] = None,
    ) -> Task:
        """Create a single standalone task."""
        task = Task(
            type=task_type,
            name=name,
            description=description,
            tool_name=tool_name,
            tool_input=tool_input or {},
            parent_task_id=parent_task_id,
        )
        self.tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus, result: str = None, error: str = None):
        """Update a task's status."""
        task = self.tasks.get(task_id)
        if not task:
            return

        if status == TaskStatus.RUNNING:
            task.start()
        elif status == TaskStatus.COMPLETED:
            task.complete(result or "")
        elif status == TaskStatus.FAILED:
            task.fail(error or "Unknown error")
        elif status == TaskStatus.CANCELLED:
            task.cancel()

    def get_plan_tasks(self, plan_id: str) -> List[Task]:
        """Get all tasks for a plan."""
        task_ids = self.plan_tasks.get(plan_id, [])
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values())

    def clear(self):
        """Clear all tasks."""
        self.tasks.clear()
        self.plan_tasks.clear()
