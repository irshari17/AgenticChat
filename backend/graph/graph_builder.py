"""
LangGraph Graph Builder — constructs the agent orchestration graph.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes.planner_node import planner_node
from graph.nodes.executor_node import executor_node
from graph.nodes.memory_node import memory_node


def should_execute(state: AgentState) -> Literal["executor", "memory"]:
    """Decide: execute tasks or go to memory/response."""
    if state.get("needs_execution") and state.get("tasks"):
        return "executor"
    return "memory"


def should_continue_execution(state: AgentState) -> Literal["executor", "memory"]:
    """Decide: continue executing more tasks or finalize."""
    if state.get("should_continue", False):
        return "executor"
    return "memory"


def build_agent_graph():
    """
    Build the LangGraph orchestration graph.
    
    Flow: User Input → Planner → [Executor loop] → Memory → Response
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("memory", memory_node)

    # Entry point
    graph.set_entry_point("planner")

    # Planner → executor or memory
    graph.add_conditional_edges(
        "planner",
        should_execute,
        {"executor": "executor", "memory": "memory"},
    )

    # Executor → loop or memory
    graph.add_conditional_edges(
        "executor",
        should_continue_execution,
        {"executor": "executor", "memory": "memory"},
    )

    # Memory → END
    graph.add_edge("memory", END)

    return graph.compile()


# Singleton
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph
