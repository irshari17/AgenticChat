"""
Planner Agent: analyzes user queries and creates structured execution plans.
"""

import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from schemas.messages import ExecutionPlan, PlanStep


class PlannerAgent(BaseAgent):
    """
    Planner Agent that breaks down user queries into actionable steps.
    It decides which tools to use and whether to spawn executor agents.
    """

    name = "planner"
    description = "I analyze user requests and create structured execution plans."

    def __init__(self, llm: LLMService, tool_executor: ToolExecutor):
        super().__init__(llm)
        self.tool_executor = tool_executor

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an execution plan for the user's query.
        
        Input:
            query: str - The user's query.
            context: str - Conversation context.
            
        Returns:
            Dict with 'plan' (ExecutionPlan) and 'response' (str).
        """
        query = input_data.get("query", "")
        context = input_data.get("context", "")

        # Get tool descriptions for planning
        tool_descriptions = self.tool_executor.get_tool_descriptions()
        tool_names = self.tool_executor.get_tool_names()

        system_prompt = self._build_planning_prompt(tool_descriptions, tool_names)

        messages = []
        if context:
            messages.append({"role": "system", "content": f"Conversation context:\n{context}"})
        messages.append({"role": "user", "content": query})

        # Get the LLM to create a plan
        try:
            result = await self.llm.complete_json(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            plan = self._parse_plan(result, query)
            return {
                "plan": plan,
                "response": result.get("reasoning", "Plan created successfully."),
                "needs_execution": len(plan.steps) > 0,
            }
        except Exception as e:
            # If planning fails, create a simple direct-response plan
            return {
                "plan": ExecutionPlan(
                    query=query,
                    steps=[],
                    reasoning=f"Planning failed: {str(e)}. Will respond directly.",
                ),
                "response": "",
                "needs_execution": False,
                "error": str(e),
            }

    def _build_planning_prompt(self, tool_descriptions: str, tool_names: List[str]) -> str:
        """Build the system prompt for planning."""
        return f"""You are an AI planning agent. Your job is to analyze user requests and create a structured execution plan.

{tool_descriptions}

You must respond with a JSON object in this exact format:
{{
    "reasoning": "Your analysis of what the user needs",
    "steps": [
        {{
            "type": "tool",
            "tool": "<tool_name>",
            "input": {{"key": "value"}},
            "reasoning": "Why this step is needed"
        }},
        {{
            "type": "agent",
            "task": "Description of the sub-task",
            "reasoning": "Why this needs an agent"
        }}
    ],
    "direct_response": null
}}

Rules:
1. If the query is a simple greeting or conversation, set "steps" to an empty array and put your response in "direct_response".
2. For tasks requiring tools, create specific steps with correct tool names: {tool_names}
3. For file_tool: include "action" ("read", "write", "list"), "path", and optionally "content" in input.
4. For web_tool: include "action" ("fetch", "search_snippet"), "url" or "query" in input.
5. For shell_tool: include "command" in input.
6. Order steps logically.
7. Be specific about what each step should accomplish.
"""

    def _parse_plan(self, result: Dict[str, Any], query: str) -> ExecutionPlan:
        """Parse LLM output into an ExecutionPlan."""
        steps = []

        # Check for direct response (no tools needed)
        if result.get("direct_response"):
            return ExecutionPlan(
                query=query,
                steps=[],
                reasoning=result.get("reasoning", "Direct response"),
            )

        raw_steps = result.get("steps", [])
        for raw_step in raw_steps:
            step = PlanStep(
                type=raw_step.get("type", "agent"),
                tool=raw_step.get("tool"),
                task=raw_step.get("task"),
                input=raw_step.get("input", {}),
                reasoning=raw_step.get("reasoning", ""),
            )
            steps.append(step)

        return ExecutionPlan(
            query=query,
            steps=steps,
            reasoning=result.get("reasoning", ""),
        )
