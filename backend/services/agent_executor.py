"""
Agent Executor — runs agents within the task execution loop.
Supports recursive planning and sub-agent spawning.
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from tasks.task import Task, TaskStatus
from memory.shared_memory import SharedMemory
import logging

logger = logging.getLogger("services.agent_executor")

StreamCallback = Optional[Callable[[Dict[str, Any]], Awaitable[None]]]


class AgentExecutorService:
    """
    High-level service that coordinates agent execution.
    Supports recursive planning when an executor decides a sub-task
    needs further decomposition.
    """

    def __init__(
        self,
        llm: LLMService,
        tool_executor: ToolExecutor,
        shared_memory: SharedMemory,
        max_depth: int = 3,
    ):
        self.llm = llm
        self.tool_executor = tool_executor
        self.shared_memory = shared_memory
        self.max_depth = max_depth
        self.executor = ExecutorAgent(llm=llm, tool_executor=tool_executor)

    async def execute_task(
        self,
        task: Task,
        context: str = "",
        session_id: Optional[str] = None,
        callback: StreamCallback = None,
        depth: int = 0,
    ) -> Dict[str, Any]:
        """Execute a single task, with optional recursive planning."""
        if depth > self.max_depth:
            return {"result": "Max recursion depth reached", "status": TaskStatus.FAILED}

        # Notify
        if callback:
            label = f"🔧 {task.tool_name}" if task.type == "tool" else f"🤖 {task.name}"
            await callback({
                "type": "task_update",
                "content": f"{'  ' * depth}Executing: {label}",
            })

        # Execute
        result = await self.executor.run({"task": task, "context": context})

        # Store result in shared memory
        if session_id:
            self.shared_memory.set(
                key=f"task_result_{task.id}",
                value=result.get("result", ""),
                source_agent="executor",
                session_id=session_id,
            )

        if callback and task.type == "tool":
            await callback({
                "type": "tool_result",
                "content": f"{'  ' * depth}Result: {result.get('result', '')[:400]}",
            })

        return result
