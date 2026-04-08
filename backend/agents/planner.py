"""
Planner Agent — decomposes queries into structured execution plans with task dependencies.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from schemas.plan import ExecutionPlan, PlanStep
import logging

logger = logging.getLogger("agents.planner")


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "I break down complex requests into structured, executable plans."

    def __init__(self, llm: LLMService, tool_executor: ToolExecutor):
        super().__init__(llm)
        self.tool_executor = tool_executor

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        context = input_data.get("context", "")

        tool_descriptions = self.tool_executor.get_tool_descriptions()
        tool_names = self.tool_executor.get_tool_names()

        system_prompt = self._build_prompt(tool_descriptions, tool_names)

        messages = []
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": query})

        try:
            result = await self.llm.complete_json(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            plan = self._parse_plan(result, query)

            logger.info(f"Plan created: {len(plan.steps)} steps, reasoning={plan.reasoning[:100]}")

            return {
                "plan": plan,
                "reasoning": result.get("reasoning", "Plan created."),
                "needs_execution": len(plan.steps) > 0,
                "direct_response": result.get("direct_response"),
            }

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return {
                "plan": ExecutionPlan(query=query, steps=[], reasoning=f"Error: {e}"),
                "reasoning": str(e),
                "needs_execution": False,
                "direct_response": None,
                "error": str(e),
            }

    def _build_prompt(self, tool_descriptions: str, tool_names: List[str]) -> str:
        return f"""You are an AI planning agent. Analyze user requests and create structured execution plans.

{tool_descriptions}

Respond with JSON in this EXACT format:
{{
    "reasoning": "Your analysis of what the user needs",
    "direct_response": null,
    "steps": [
        {{
            "id": "1",
            "type": "tool",
            "tool": "<tool_name>",
            "input": {{"key": "value"}},
            "depends_on": [],
            "reasoning": "Why this step"
        }},
        {{
            "id": "2",
            "type": "agent",
            "task": "Description of sub-task",
            "depends_on": ["1"],
            "reasoning": "Why this step"
        }}
    ]
}}

RULES:
1. If simple conversation (greeting, basic question), set steps=[] and direct_response="your answer".
2. Available tools: {tool_names}
3. file_tool input: {{"action": "read|write|list", "path": "filename", "content": "text"}}
4. web_tool input: {{"action": "fetch|search_snippet", "url": "...", "query": "..."}}
5. shell_tool input: {{"command": "..."}}
6. Use "depends_on" to reference step "id" values for task ordering.
7. Each step needs a unique "id" string.
8. Maximum 10 steps."""

    def _parse_plan(self, result: Dict[str, Any], query: str) -> ExecutionPlan:
        # Check for direct response
        if result.get("direct_response"):
            return ExecutionPlan(
                query=query,
                steps=[],
                reasoning=result.get("reasoning", ""),
                direct_response=result["direct_response"],
            )

        steps = []
        id_map: Dict[str, str] = {}  # raw_id -> PlanStep.step_id

        raw_steps = result.get("steps", [])
        if not isinstance(raw_steps, list):
            raw_steps = []

        for raw in raw_steps:
            if not isinstance(raw, dict):
                continue

            step = PlanStep(
                type=raw.get("type", "agent"),
                tool=raw.get("tool"),
                task=raw.get("task"),
                input=raw.get("input") if isinstance(raw.get("input"), dict) else {},
                reasoning=raw.get("reasoning", ""),
                depends_on=[],  # will resolve below
            )

            raw_id = str(raw.get("id", step.step_id))
            id_map[raw_id] = step.step_id
            steps.append((raw, step))

        # Resolve dependencies
        final_steps = []
        for raw, step in steps:
            raw_deps = raw.get("depends_on", [])
            if isinstance(raw_deps, list):
                step.depends_on = [id_map[str(d)] for d in raw_deps if str(d) in id_map]
            final_steps.append(step)

        return ExecutionPlan(
            query=query,
            steps=final_steps,
            reasoning=result.get("reasoning", ""),
        )
