"""
Base tool interface that all tools must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    Every tool must define a name, description, and implement the run method.
    """

    name: str = "base_tool"
    description: str = "Base tool"

    @abstractmethod
    async def run(self, input: Dict[str, Any]) -> str:
        """
        Execute the tool with given input.
        
        Args:
            input: Dictionary of tool-specific parameters.
            
        Returns:
            String result of tool execution.
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return the tool's input schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {},
        }

    def __repr__(self):
        return f"<Tool: {self.name}>"
