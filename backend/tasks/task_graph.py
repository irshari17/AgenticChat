"""
Task Graph — DAG-based task dependency management.
Tasks can depend on other tasks, enabling parallel execution of independent steps.
"""

from typing import Dict, List, Set, Optional
from tasks.task import Task, TaskStatus
import logging

logger = logging.getLogger("tasks.graph")


class TaskGraph:
    """
    Directed Acyclic Graph for task scheduling.
    Manages dependencies between tasks and determines execution order.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.edges: Dict[str, Set[str]] = {}  # task_id -> set of task_ids it depends on
        self.reverse_edges: Dict[str, Set[str]] = {}  # task_id -> set of task_ids that depend on it

    def add_task(self, task: Task):
        """Add a task to the graph."""
        self.tasks[task.id] = task
        if task.id not in self.edges:
            self.edges[task.id] = set()
        if task.id not in self.reverse_edges:
            self.reverse_edges[task.id] = set()

    def add_dependency(self, task_id: str, depends_on: str):
        """Add a dependency: task_id depends on depends_on."""
        if task_id not in self.edges:
            self.edges[task_id] = set()
        if depends_on not in self.reverse_edges:
            self.reverse_edges[depends_on] = set()

        self.edges[task_id].add(depends_on)
        self.reverse_edges[depends_on].add(task_id)

    def get_ready_tasks(self) -> List[Task]:
        """
        Get all tasks that are ready to execute
        (all dependencies completed, task is still pending).
        """
        ready = []
        for task_id, task in self.tasks.items():
            if task.status != TaskStatus.PENDING:
                continue

            deps = self.edges.get(task_id, set())
            all_deps_done = all(
                self.tasks.get(d) and self.tasks[d].status == TaskStatus.COMPLETED
                for d in deps
            )

            if all_deps_done:
                ready.append(task)

        return ready

    def get_next_tasks(self) -> List[Task]:
        """Get the next batch of executable tasks (for parallel execution)."""
        return self.get_ready_tasks()

    def is_complete(self) -> bool:
        """Check if all tasks are in a terminal state."""
        return all(t.is_terminal for t in self.tasks.values())

    def has_failed(self) -> bool:
        """Check if any task has failed."""
        return any(t.status == TaskStatus.FAILED for t in self.tasks.values())

    def get_results(self) -> Dict[str, Optional[str]]:
        """Get results of all completed tasks."""
        return {
            tid: t.result
            for tid, t in self.tasks.items()
            if t.status == TaskStatus.COMPLETED
        }

    def get_status_summary(self) -> Dict[str, int]:
        """Get count of tasks by status."""
        summary: Dict[str, int] = {}
        for t in self.tasks.values():
            summary[t.status.value] = summary.get(t.status.value, 0) + 1
        return summary

    def topological_order(self) -> List[str]:
        """Return task IDs in topological order."""
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dep in self.edges.get(node, set()):
                dfs(dep)
            order.append(node)

        for tid in self.tasks:
            dfs(tid)

        return order

    def __len__(self):
        return len(self.tasks)
