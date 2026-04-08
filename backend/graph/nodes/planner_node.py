"""
Planner Node — generates execution plan from user query.
"""

import json
from typing import Dict, Any
from graph.state import AgentState
from agents.planner import PlannerAgent
from core.dependencies import get_llm_service, get_tool_executor, get_agent_registry
import logging

logger = logging.getLogger("graph.planner")


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """Runs the Planner Agent to create a structured execution plan."""
    llm = get_llm_service()
    tool_executor = get_tool_executor()
    registry = get_agent_registry()
    planner = PlannerAgent(llm=llm, tool_executor=tool_executor)

    callback = state.get("stream_callback")
    if callback:
        await callback({"type": "status", "content": "🧠 Planner creating execution plan..."})

    agent_instance = registry.spawn("planner")

    result = await planner.run({
        "query": state.get("user_query", ""),
        "context": state.get("context", ""),
    })

    agent_instance.complete_task()

    plan = result.get("plan")
    needs_execution = result.get("needs_execution", False)
    direct_response = result.get("direct_response")

    # Build task list for executor
    tasks = []
    if plan and plan.steps:
        for step in plan.steps:
            tasks.append({
                "type": step.type,
                "tool_name": step.tool,
                "tool_input": step.input or {},
                "task_description": step.task or step.reasoning,
                "reasoning": step.reasoning,
                "depends_on": step.depends_on,
                "status": "pending",
                "result": None,
            })

    # Stream plan to client
    if callback and plan and plan.steps:
        plan_info = {
            "reasoning": plan.reasoning,
            "steps": [
                {"type": s.type, "tool": s.tool, "task": s.task, "reasoning": s.reasoning}
                for s in plan.steps
            ],
        }
        await callback({"type": "plan", "content": json.dumps(plan_info)})

    logger.info(f"Plan created: {len(tasks)} tasks, needs_execution={needs_execution}")

    return {
        "plan": plan.model_dump() if plan else None,
        "tasks": tasks,
        "current_step_index": 0,
        "needs_execution": needs_execution,
        "direct_response": direct_response or (plan.direct_response if plan else None),
        "should_continue": needs_execution and len(tasks) > 0,
    }
