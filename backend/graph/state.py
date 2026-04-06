"""
LangGraph State: defines the shared state object passed between graph nodes.
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from schemas.messages import ExecutionPlan, ChatMessage
from tasks.task import Task


class AgentState(TypedDict):
    """
    Shared state for the LangGraph agent orchestration.
    All nodes read from and write to this state.
    """
    # User input
    user_query: str
    session_id: str

    # Chat context
    context: str
    chat_history: List[Dict[str, str]]

    # Planning
    plan: Optional[Dict[str, Any]]
    current_step_index: int
    needs_execution: bool

    # Execution
    tasks: List[Dict[str, Any]]
    current_task: Optional[Dict[str, Any]]
    task_results: List[Dict[str, Any]]

    # Tool execution
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_result: Optional[str]

    # Response generation
    final_response: str
    response_chunks: List[str]

    # Control flow
    should_continue: bool
    error: Optional[str]
    direct_response: Optional[str]

    # Streaming callback
    stream_callback: Optional[Any]
