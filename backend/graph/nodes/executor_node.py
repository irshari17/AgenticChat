"""
Executor Node for LangGraph.
"""

from typing import Dict, Any
from graph.state import AgentState
from agents.executor import ExecutorAgent
from tasks.task import Task, TaskStatus
from core.dependencies import get_llm_service, get_tool_executor


async def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the current task in the plan."""
    llm = get_llm_service()
    tool_executor = get_tool_executor()
    executor = ExecutorAgent(llm=llm, tool_executor=tool_executor)

    tasks = list(state.get("tasks", []))
    current_index = state.get("current_step_index", 0)
    task_results = list(state.get("task_results", []))
    callback = state.get("stream_callback")

    if current_index >= len(tasks):
        return {"should_continue": False, "task_results": task_results}

    current_task_data = tasks[current_index]

    task = Task(
        type=current_task_data["type"],
        name=current_task_data.get("tool_name") or current_task_data.get("task_description", "task"),
        description=current_task_data.get("task_description", ""),
        tool_name=current_task_data.get("tool_name"),
        tool_input=current_task_data.get("tool_input", {}),
    )

    if callback:
        label = f"🔧 {task.tool_name}" if task.type == "tool" else f"🤖 {task.name}"
        await callback({
            "type": "task_update",
            "content": f"Executing step {current_index + 1}/{len(tasks)}: {label}",
        })

    context = state.get("context", "")
    if task_results:
        prev = "\n".join([f"Previous result: {r.get('result', 'N/A')[:200]}" for r in task_results])
        context = f"{context}\n{prev}"

    result = await executor.run({"task": task, "context": context})

    task_result = {
        "step_index": current_index,
        "type": current_task_data["type"],
        "tool_name": current_task_data.get("tool_name"),
        "result": result.get("result", ""),
        "status": result.get("status", TaskStatus.COMPLETED).value
        if hasattr(result.get("status", ""), "value")
        else str(result.get("status", "")),
    }
    task_results.append(task_result)

    if callback and current_task_data["type"] == "tool":
        await callback({
            "type": "tool_result",
            "content": f"Tool '{current_task_data.get('tool_name')}': {result.get('result', '')[:500]}",
        })

    next_index = current_index + 1
    should_continue = next_index < len(tasks)

    return {
        "tasks": tasks,
        "current_step_index": next_index,
        "task_results": task_results,
        "should_continue": should_continue,
        "current_task": task_result,
    }
