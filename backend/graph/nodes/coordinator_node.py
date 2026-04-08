"""
Coordinator Node — classifies requests and decides execution path.
"""

import json
from typing import Dict, Any
from graph.state import AgentState
from agents.coordinator import CoordinatorAgent
from core.dependencies import get_llm_service, get_agent_registry
import logging

logger = logging.getLogger("graph.coordinator")


async def coordinator_node(state: AgentState) -> Dict[str, Any]:
    """
    Entry point of the graph. The Coordinator classifies the user's request
    and decides whether to respond directly or invoke the planner.
    """
    llm = get_llm_service()
    registry = get_agent_registry()
    coordinator = CoordinatorAgent(llm=llm)

    callback = state.get("stream_callback")
    if callback:
        await callback({"type": "coordinator", "content": "🎯 Coordinator analyzing your request..."})

    # Register coordinator in agent registry
    agent_instance = registry.spawn("coordinator")

    result = await coordinator.run({
        "query": state.get("user_query", ""),
        "context": state.get("context", ""),
    })

    agent_instance.complete_task()

    classification = result.get("classification", "direct")
    needs_planning = result.get("needs_planning", False)

    if callback:
        if needs_planning:
            await callback({"type": "coordinator", "content": f"📋 Complex request detected — invoking planner (complexity: {result.get('complexity', 'unknown')})"})
        else:
            await callback({"type": "coordinator", "content": "💬 Simple request — generating direct response"})

    logger.info(f"Coordinator decision: classification={classification}, needs_planning={needs_planning}")

    return {
        "classification": classification,
        "needs_planning": needs_planning,
    }
