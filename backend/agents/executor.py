"""
Executor Agent — executes individual tasks (tool calls or agent reasoning).
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from tasks.task import Task, TaskStatus
import logging

logger = logging.getLogger("agents.executor")


class ExecutorAgent(BaseAgent):
    name = "executor"
    description = "I execute individual tasks from the plan."

    def __init__(self, llm: LLMService, tool_executor: ToolExecutor):
        super().__init__(llm)
        self.tool_executor = tool_executor

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        task: Task = input_data.get("task")
        context = input_data.get("context", "")

        if not task:
            return {"result": "Error: no task provided", "status": TaskStatus.FAILED}

        task.start()

        try:
            if task.type == "tool":
                result = await self._execute_tool(task)
            elif task.type == "agent":
                result = await self._execute_agent_task(task, context)
            else:
                result = f"Unknown task type: {task.type}"

            task.complete(result)
            logger.info(f"Task completed: {task.name} ({len(result)} chars)")
            return {"result": result, "status": TaskStatus.COMPLETED}

        except Exception as e:
            error = f"Execution error: {str(e)}"
            task.fail(error)
            logger.error(f"Task failed: {task.name} — {error}")

            # Retry logic
            if task.can_retry:
                task.retry()
                logger.info(f"Retrying task: {task.name} (attempt {task.retry_count})")
                return await self.run(input_data)

            return {"result": error, "status": TaskStatus.FAILED}

    async def _execute_tool(self, task: Task) -> str:
        if not task.tool_name:
            return "Error: no tool name specified"
        task.add_log(f"Calling tool: {task.tool_name} with {task.tool_input}")
        return await self.tool_executor.execute(task.tool_name, task.tool_input or {})

    async def _execute_agent_task(self, task: Task, context: str) -> str:
        system_prompt = (
            "You are an executor agent. Complete the assigned task thoroughly and accurately. "
            "Provide a detailed, helpful response."
        )
        messages = []
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({
            "role": "user",
            "content": f"Task: {task.name}\nDescription: {task.description}\n\nComplete this task.",
        })
        return await self.llm.complete(messages=messages, system_prompt=system_prompt)
