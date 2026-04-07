"""
Planner Agent: analyzes queries and creates structured execution plans.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from schemas.messages import ExecutionPlan, PlanStep


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "Analyzes requests and creates execution plans."

    def __init__(self, llm: LLMService, tool_executor: ToolExecutor):
        super().__init__(llm)
        self.tool_executor = tool_executor

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        context = input_data.get("context", "")

        tool_descriptions = self.tool_executor.get_tool_descriptions()
        tool_names = self.tool_executor.get_tool_names()

        system_prompt = self._build_planning_prompt(tool_descriptions, tool_names)

        messages = []
        if context:
            messages.append({"role": "system", "content": f"Conversation context:\n{context}"})
        messages.append({"role": "user", "content": query})

        try:
            result = await self.llm.complete_json(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            plan = self._parse_plan(result, query)
            return {
                "plan": plan,
                "response": result.get("reasoning", "Plan created."),
                "needs_execution": len(plan.steps) > 0,
            }
        except Exception as e:
            return {
                "plan": ExecutionPlan(query=query, steps=[], reasoning=f"Error: {str(e)}"),
                "response": "",
                "needs_execution": False,
                "error": str(e),
            }

    def _build_planning_prompt(self, tool_descriptions: str, tool_names: List[str]) -> str:
        return f"""You are an AI planning agent. Analyze user requests and create execution plans.

{tool_descriptions}

Respond with JSON in this exact format:
{{
    "reasoning": "Your analysis",
    "steps": [
        {{
            "type": "tool",
            "tool": "<tool_name>",
            "input": {{"key": "value"}},
            "reasoning": "Why this step"
        }}
    ],
    "direct_response": null
}}

Rules:
1. For simple conversation/greetings, set "steps" to [] and "direct_response" to your response text.
2. Available tool names: {tool_names}
3. file_tool input: {{"action": "read|write|list", "path": "...", "content": "..."}}
4. web_tool input: {{"action": "fetch|search_snippet", "url": "...", "query": "..."}}
5. shell_tool input: {{"command": "..."}}
6. Be specific about each step."""

    def _parse_plan(self, result: Dict[str, Any], query: str) -> ExecutionPlan:
        if result.get("direct_response"):
            return ExecutionPlan(query=query, steps=[], reasoning=result.get("reasoning", ""))

        steps = []
        for raw in result.get("steps", []):
            if isinstance(raw, dict):
                steps.append(PlanStep(
                    type=raw.get("type", "agent"),
                    tool=raw.get("tool"),
                    task=raw.get("task"),
                    input=raw.get("input", {}),
                    reasoning=raw.get("reasoning", ""),
                ))

        return ExecutionPlan(query=query, steps=steps, reasoning=result.get("reasoning", ""))
