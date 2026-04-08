"""
Base Tool interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool"

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> str:
        pass

    def get_schema(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description, "parameters": {}}

    def __repr__(self):
        return f"<Tool: {self.name}>"
