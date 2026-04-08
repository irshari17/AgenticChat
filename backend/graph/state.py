"""
LangGraph State — the shared state object passed through all graph nodes.
"""

from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict, total=False):
    # Input
    user_query: str
    session_id: str

    # Context
    context: str
    chat_history: List[Dict[str, str]]

    # Coordinator
    classification: str
    needs_planning: bool

    # Planning
    plan: Optional[Dict[str, Any]]
    current_step_index: int
    needs_execution: bool

    # Tasks
    tasks: List[Dict[str, Any]]
    current_task: Optional[Dict[str, Any]]
    task_results: List[Dict[str, Any]]

    # Tool
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_result: Optional[str]

    # Response
    final_response: str
    response_chunks: List[str]
    direct_response: Optional[str]

    # Control
    should_continue: bool
    error: Optional[str]

    # Streaming
    stream_callback: Optional[Any]
