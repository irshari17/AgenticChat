"""
Tool Node for direct tool execution.
"""

from typing import Dict, Any
from graph.state import AgentState
from core.dependencies import get_tool_executor


async def tool_node(state: AgentState) -> Dict[str, Any]:
    """Executes a single tool directly."""
    tool_executor = get_tool_executor()
    tool_name = state.get("tool_name")
    tool_input = state.get("tool_input", {})
    callback = state.get("stream_callback")

    if not tool_name:
        return {"tool_result": "Error: no tool specified"}

    if callback:
        await callback({"type": "tool_call", "content": f"Calling tool: {tool_name}"})

    result = await tool_executor.execute(tool_name, tool_input)

    if callback:
        await callback({"type": "tool_result", "content": f"Result: {result[:500]}"})

    return {"tool_result": result}
