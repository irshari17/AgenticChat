"""
Executor Node — processes tasks from the plan one at a time.
"""

from typing import Dict, Any
from graph.state import AgentState
from agents.executor import ExecutorAgent
from tasks.task import Task, TaskStatus
from core.dependencies import get_llm_service, get_tool_executor, get_agent_registry, get_shared_memory
import logging

logger = logging.getLogger("graph.executor")


async def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the current task in the task list."""
    llm = get_llm_service()
    tool_executor = get_tool_executor()
    registry = get_agent_registry()
    shared_mem = get_shared_memory()
    executor = ExecutorAgent(llm=llm, tool_executor=tool_executor)

    tasks = list(state.get("tasks", []))
    current_index = state.get("current_step_index", 0)
    task_results = list(state.get("task_results", []))
    callback = state.get("stream_callback")
    session_id = state.get("session_id", "default")

    if current_index >= len(tasks):
        return {"should_continue": False, "task_results": task_results}

    current_task_data = tasks[current_index]

    # Create Task object
    task = Task(
        type=current_task_data["type"],
        name=current_task_data.get("tool_name") or current_task_data.get("task_description", "task"),
        description=current_task_data.get("task_description", ""),
        tool_name=current_task_data.get("tool_name"),
        tool_input=current_task_data.get("tool_input", {}),
    )

    # Register executor agent
    agent_instance = registry.spawn("executor")
    agent_instance.assign_task(task.id)

    # Stream status
    if callback:
        label = f"🔧 {task.tool_name}" if task.type == "tool" else f"🤖 {task.name}"
        await callback({
            "type": "task_update",
            "content": f"Step {current_index + 1}/{len(tasks)}: {label}",
        })
        if task.type == "tool":
            await callback({
                "type": "tool_call",
                "content": f"Calling tool: {task.tool_name} with {task.tool_input}",
            })

    # Build context from previous results
    context = state.get("context", "")
    if task_results:
        prev = "\n".join([f"Step {r['step_index']+1} result: {r.get('result', '')[:300]}" for r in task_results])
        context = f"{context}\n\nPrevious step results:\n{prev}"

    # Execute
    result = await executor.run({"task": task, "context": context})

    agent_instance.complete_task()

    # Store in shared memory
    shared_mem.set(
        key=f"task_{current_index}_result",
        value=result.get("result", ""),
        source_agent="executor",
        session_id=session_id,
    )

    # Record result
    task_result = {
        "step_index": current_index,
        "type": current_task_data["type"],
        "tool_name": current_task_data.get("tool_name"),
        "task_description": current_task_data.get("task_description", ""),
        "result": result.get("result", ""),
        "status": result.get("status", TaskStatus.COMPLETED).value
        if hasattr(result.get("status"), "value") else str(result.get("status", "")),
        "agent_id": agent_instance.agent_id,
    }
    task_results.append(task_result)

    # Stream result
    if callback and current_task_data["type"] == "tool":
        await callback({
            "type": "tool_result",
            "content": f"Result from '{current_task_data.get('tool_name', 'tool')}': {result.get('result', '')[:500]}",
        })

    next_index = current_index + 1
    should_continue = next_index < len(tasks)

    logger.info(f"Task {current_index + 1}/{len(tasks)} completed. Continue: {should_continue}")

    return {
        "tasks": tasks,
        "current_step_index": next_index,
        "task_results": task_results,
        "should_continue": should_continue,
        "current_task": task_result,
    }
