"""
Executor Agent: executes individual tasks/steps from the plan.
Can call tools and recursively invoke the planner for complex sub-tasks.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from tasks.task import Task, TaskStatus


class ExecutorAgent(BaseAgent):
    """
    Executor Agent that carries out individual plan steps.
    Handles tool calls and agent-type tasks.
    """

    name = "executor"
    description = "I execute individual tasks from the plan, including tool calls and sub-tasks."

    def __init__(self, llm: LLMService, tool_executor: ToolExecutor):
        super().__init__(llm)
        self.tool_executor = tool_executor

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Input:
            task: Task object to execute.
            context: str - Additional context.
            
        Returns:
            Dict with 'result' (str), 'status' (TaskStatus).
        """
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
            return {"result": result, "status": TaskStatus.COMPLETED}

        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            task.fail(error_msg)
            return {"result": error_msg, "status": TaskStatus.FAILED}

    async def _execute_tool(self, task: Task) -> str:
        """Execute a tool-type task."""
        tool_name = task.tool_name
        tool_input = task.tool_input or {}

        if not tool_name:
            return "Error: no tool name specified"

        task.add_log(f"Executing tool: {tool_name} with input: {tool_input}")
        result = await self.tool_executor.execute(tool_name, tool_input)
        task.add_log(f"Tool result: {result[:200]}...")
        return result

    async def _execute_agent_task(self, task: Task, context: str) -> str:
        """Execute an agent-type task using LLM reasoning."""
        system_prompt = (
            "You are an executor agent. Complete the given task thoroughly. "
            "Provide a detailed and helpful response."
        )

        messages = []
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({
            "role": "user",
            "content": f"Task: {task.name}\nDescription: {task.description}\n\nPlease complete this task.",
        })

        task.add_log("Executing agent task with LLM")
        result = await self.llm.complete(
            messages=messages,
            system_prompt=system_prompt,
        )
        return result
