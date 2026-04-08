"""
Coordinator Agent — the supervisor that manages the entire execution lifecycle.
Decides whether to respond directly or invoke the multi-agent workflow.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.llm import LLMService
import logging

logger = logging.getLogger("agents.coordinator")


class CoordinatorAgent(BaseAgent):
    name = "coordinator"
    description = (
        "I am the Coordinator. I analyze incoming requests and decide "
        "whether to respond directly or invoke the planning/execution pipeline."
    )

    CLASSIFICATION_PROMPT = """You are a request classifier for an AI agent system.

Analyze the user's message and classify it into one of these categories:
1. "direct" — Simple greeting, conversation, question that needs no tools (e.g., "hello", "what is Python?")
2. "plan" — Complex request that needs tools or multi-step execution (e.g., "write a file", "fetch a URL", "run a command", "create something and then analyze it")

Respond with ONLY valid JSON:
{
    "classification": "direct" or "plan",
    "reasoning": "Brief explanation",
    "complexity": "low" or "medium" or "high"
}"""

    def __init__(self, llm: LLMService):
        super().__init__(llm)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the user's request and decide the execution path.
        """
        query = input_data.get("query", "")
        context = input_data.get("context", "")

        logger.info(f"Coordinator classifying: {query[:100]}...")

        messages = []
        if context:
            messages.append({"role": "system", "content": f"Chat context:\n{context}"})
        messages.append({"role": "user", "content": query})

        try:
            result = await self.llm.complete_json(
                messages=messages,
                system_prompt=self.CLASSIFICATION_PROMPT,
                temperature=0.1,
            )

            classification = result.get("classification", "direct")
            reasoning = result.get("reasoning", "")
            complexity = result.get("complexity", "low")

            logger.info(f"Classification: {classification} (complexity={complexity})")

            return {
                "classification": classification,
                "reasoning": reasoning,
                "complexity": complexity,
                "needs_planning": classification == "plan",
            }

        except Exception as e:
            logger.error(f"Coordinator classification failed: {e}")
            # Default to planning on error (safer)
            return {
                "classification": "plan",
                "reasoning": f"Classification failed: {str(e)}, defaulting to plan",
                "complexity": "medium",
                "needs_planning": True,
            }
