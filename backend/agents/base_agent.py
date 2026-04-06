"""
Base Agent: abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from services.llm import LLMService


class BaseAgent(ABC):
    """
    Abstract base class for agents.
    Agents use the LLM to reason and produce structured outputs.
    """

    name: str = "base_agent"
    description: str = "Base agent"

    def __init__(self, llm: LLMService):
        self.llm = llm

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic.
        
        Args:
            input_data: Input context and parameters.
            
        Returns:
            Dictionary with agent's output.
        """
        pass

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent."""
        return f"You are {self.name}. {self.description}"
