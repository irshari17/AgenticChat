"""
Tool Executor: routes tool calls to the appropriate tool implementation.
"""

from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool


class ToolExecutor:
    """
    Executor that manages and dispatches tool calls.
    Tools are registered and looked up by name.
    """

    def __init__(self, tools: List[BaseTool] = None):
        self.tools: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: BaseTool):
        """Register a tool by its name."""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)

    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given input.
        
        Args:
            tool_name: Name of the tool to execute.
            tool_input: Input parameters for the tool.
            
        Returns:
            String result of the tool execution.
        """
        tool = self.tools.get(tool_name)
        if not tool:
            available = ", ".join(self.tools.keys())
            return f"Error: Tool '{tool_name}' not found. Available tools: {available}"

        try:
            result = await tool.run(tool_input)
            return result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all available tools for LLM context."""
        if not self.tools:
            return "No tools available."

        lines = ["Available tools:"]
        for name, tool in self.tools.items():
            schema = tool.get_schema()
            params = schema.get("parameters", {})
            param_str = ", ".join(
                f"{k}: {v.get('description', v.get('type', 'any'))}"
                for k, v in params.items()
            )
            lines.append(f"  - {name}: {tool.description}")
            if param_str:
                lines.append(f"    Parameters: {param_str}")
        return "\n".join(lines)

    def get_tool_names(self) -> List[str]:
        """Get list of all available tool names."""
        return list(self.tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas of all tools for LLM function calling."""
        return [tool.get_schema() for tool in self.tools.values()]
