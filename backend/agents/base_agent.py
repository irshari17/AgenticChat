"""
Base Agent interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from services.llm import LLMService


class BaseAgent(ABC):
    name: str = "base_agent"
    description: str = "Base agent"

    def __init__(self, llm: LLMService):
        self.llm = llm

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def __repr__(self):
        return f"<Agent: {self.name}>"
