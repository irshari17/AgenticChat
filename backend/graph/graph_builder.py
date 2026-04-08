"""
LangGraph Graph Builder — constructs the complete agent orchestration graph.

Flow:
    User → Coordinator → [Planner] → [Executor loop] → Memory → Response
    
The Coordinator decides whether to invoke the Planner or go straight to Memory.
The Executor loops through all plan steps before going to Memory.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes.coordinator_node import coordinator_node
from graph.nodes.planner_node import planner_node
from graph.nodes.executor_node import executor_node
from graph.nodes.memory_node import memory_node
import logging

logger = logging.getLogger("graph.builder")


def coordinator_router(state: AgentState) -> Literal["planner", "memory"]:
    """Route from Coordinator: needs planning or direct response."""
    if state.get("needs_planning", False):
        return "planner"
    return "memory"


def planner_router(state: AgentState) -> Literal["executor", "memory"]:
    """Route from Planner: has tasks to execute or direct response."""
    if state.get("needs_execution") and state.get("tasks"):
        return "executor"
    return "memory"


def executor_router(state: AgentState) -> Literal["executor", "memory"]:
    """Route from Executor: more tasks or done."""
    if state.get("should_continue", False):
        return "executor"
    return "memory"


def build_agent_graph():
    """
    Build the full LangGraph agent orchestration graph.
    
    Graph structure:
        ┌──────────────┐
        │  Coordinator  │ (entry point)
        └──────┬───────┘
               │
        ┌──────┴───────┐
        ▼              ▼
    ┌────────┐    ┌────────┐
    │Planner │    │ Memory │ (direct response)
    └───┬────┘    └────┬───┘
        │              │
        ▼              ▼
    ┌────────┐       END
    │Executor│◄──┐
    └───┬────┘   │
        │        │ (loop)
        ├────────┘
        ▼
    ┌────────┐
    │ Memory │
    └───┬────┘
        ▼
       END
    """
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("memory", memory_node)

    # Entry point: always start with coordinator
    graph.set_entry_point("coordinator")

    # Coordinator → planner or memory
    graph.add_conditional_edges(
        "coordinator",
        coordinator_router,
        {"planner": "planner", "memory": "memory"},
    )

    # Planner → executor or memory
    graph.add_conditional_edges(
        "planner",
        planner_router,
        {"executor": "executor", "memory": "memory"},
    )

    # Executor → executor (loop) or memory
    graph.add_conditional_edges(
        "executor",
        executor_router,
        {"executor": "executor", "memory": "memory"},
    )

    # Memory → END
    graph.add_edge("memory", END)

    compiled = graph.compile()
    logger.info("✅ Agent graph compiled successfully")
    return compiled


# Singleton
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph
