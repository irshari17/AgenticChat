"""
Task Manager — creates, tracks, and schedules tasks.
"""

from typing import Dict, List, Optional
from tasks.task import Task, TaskStatus
from tasks.task_graph import TaskGraph
from schemas.plan import ExecutionPlan
import logging

logger = logging.getLogger("tasks.manager")


class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.graphs: Dict[str, TaskGraph] = {}  # plan_id -> TaskGraph

    def create_graph_from_plan(self, plan: ExecutionPlan) -> TaskGraph:
        """Create a TaskGraph from an ExecutionPlan with dependency resolution."""
        graph = TaskGraph()
        step_id_to_task_id: Dict[str, str] = {}

        # Create tasks
        for step in plan.steps:
            task = Task(
                type=step.type,
                name=step.tool or step.task or "unnamed",
                description=step.reasoning,
                tool_name=step.tool,
                tool_input=step.input or {},
                depends_on=step.depends_on,
                metadata={"plan_id": plan.plan_id, "step_id": step.step_id},
            )
            graph.add_task(task)
            self.tasks[task.id] = task
            step_id_to_task_id[step.step_id] = task.id

        # Wire dependencies
        for step in plan.steps:
            task_id = step_id_to_task_id[step.step_id]
            for dep_step_id in step.depends_on:
                dep_task_id = step_id_to_task_id.get(dep_step_id)
                if dep_task_id:
                    graph.add_dependency(task_id, dep_task_id)

        self.graphs[plan.plan_id] = graph
        logger.info(f"TaskGraph created: {len(graph)} tasks, plan={plan.plan_id}")
        return graph

    def create_linear_tasks(self, plan: ExecutionPlan) -> List[Task]:
        """Create tasks in linear order (fallback when no explicit dependencies)."""
        tasks = []
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
        logger.info(f"Linear tasks created: {len(tasks)} tasks")
        return tasks

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def clear(self):
        self.tasks.clear()
        self.graphs.clear()
