"""
LangGraph Graph Builder: constructs the agent orchestration graph.
Defines nodes, edges, and conditional routing.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes.planner_node import planner_node
from graph.nodes.executor_node import executor_node
from graph.nodes.tool_node import tool_node
from graph.nodes.memory_node import memory_node


def should_execute(state: AgentState) -> Literal["executor", "memory"]:
    """
    Conditional edge: decide whether to execute tasks or go straight to memory/response.
    """
    if state.get("needs_execution") and state.get("tasks"):
        return "executor"
    return "memory"


def should_continue_execution(state: AgentState) -> Literal["executor", "memory"]:
    """
    Conditional edge: decide whether to continue executing more tasks or finalize.
    """
    if state.get("should_continue", False):
        return "executor"
    return "memory"


def build_agent_graph() -> StateGraph:
    """
    Build and compile the LangGraph agent orchestration graph.
    
    Flow:
        User Input → Planner → [Executor → Tool]* → Memory → Response
    
    The planner decides if tools are needed.
    The executor loops through all plan steps.
    Memory stores results and generates the final response.
    """

    # Create the graph with our state type
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("memory", memory_node)

    # Set the entry point
    graph.set_entry_point("planner")

    # Planner → conditional → executor or memory
    graph.add_conditional_edges(
        "planner",
        should_execute,
        {
            "executor": "executor",
            "memory": "memory",
        },
    )

    # Executor → conditional → loop back to executor or go to memory
    graph.add_conditional_edges(
        "executor",
        should_continue_execution,
        {
            "executor": "executor",
            "memory": "memory",
        },
    )

    # Memory → END
    graph.add_edge("memory", END)

    # Compile the graph
    compiled = graph.compile()
    return compiled


# Singleton compiled graph
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph
