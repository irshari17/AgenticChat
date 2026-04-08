"""
Tool Executor — routes tool calls to implementations.
"""

from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool
import logging

logger = logging.getLogger("services.tool_executor")


class ToolExecutor:
    def __init__(self, tools: List[BaseTool] = None):
        self.tools: Dict[str, BaseTool] = {}
        for t in (tools or []):
            self.register(t)

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            available = ", ".join(self.tools.keys())
            return f"Error: Tool '{tool_name}' not found. Available: {available}"
        try:
            logger.info(f"Executing tool: {tool_name}")
            result = await tool.run(tool_input)
            logger.info(f"Tool '{tool_name}' completed ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {e}")
            return f"Tool execution error: {str(e)}"

    def get_tool_descriptions(self) -> str:
        if not self.tools:
            return "No tools available."
        lines = ["Available tools:"]
        for name, tool in self.tools.items():
            schema = tool.get_schema()
            params = schema.get("parameters", {})
            param_str = ", ".join(f"{k}" for k in params.keys())
            lines.append(f"  - {name}: {tool.description} (params: {param_str})")
        return "\n".join(lines)

    def get_tool_names(self) -> List[str]:
        return list(self.tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [t.get_schema() for t in self.tools.values()]
