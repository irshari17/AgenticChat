"""
Planner Node for LangGraph.
"""

import json
from typing import Dict, Any
from graph.state import AgentState
from agents.planner import PlannerAgent
from core.dependencies import get_llm_service, get_tool_executor


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """Runs the Planner Agent to generate an execution plan."""
    llm = get_llm_service()
    tool_executor = get_tool_executor()
    planner = PlannerAgent(llm=llm, tool_executor=tool_executor)

    callback = state.get("stream_callback")
    if callback:
        await callback({"type": "status", "content": "🧠 Planning your request..."})

    result = await planner.run({
        "query": state.get("user_query", ""),
        "context": state.get("context", ""),
    })

    plan = result.get("plan")
    needs_execution = result.get("needs_execution", False)

    tasks = []
    if plan and plan.steps:
        for step in plan.steps:
            tasks.append({
                "type": step.type,
                "tool_name": step.tool,
                "tool_input": step.input or {},
                "task_description": step.task or step.reasoning,
                "reasoning": step.reasoning,
                "status": "pending",
                "result": None,
            })

    if callback and plan and plan.steps:
        plan_info = {
            "reasoning": plan.reasoning,
            "steps": [
                {"type": s.type, "tool": s.tool, "task": s.task, "reasoning": s.reasoning}
                for s in plan.steps
            ],
        }
        await callback({"type": "plan", "content": json.dumps(plan_info)})

    direct_response = None
    if plan and not plan.steps:
        direct_response = result.get("response", "")

    return {
        "plan": plan.model_dump() if plan else None,
        "tasks": tasks,
        "current_step_index": 0,
        "needs_execution": needs_execution,
        "direct_response": direct_response,
        "should_continue": needs_execution,
    }
