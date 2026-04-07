"""
Dependency injection — provides shared service instances.
"""

from memory.memory_store import MemoryStore
from memory.session_memory import SessionMemoryManager
from tasks.task_manager import TaskManager
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from tools.file_tool import FileTool
from tools.web_tool import WebTool
from tools.shell_tool import ShellTool
from core.config import settings

# Singleton instances (module-level)
_memory_store: MemoryStore = None  # type: ignore
_session_manager: SessionMemoryManager = None  # type: ignore
_task_manager: TaskManager = None  # type: ignore
_llm_service: LLMService = None  # type: ignore


def get_memory_store() -> MemoryStore:
    """Singleton memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore(max_items=settings.MAX_MEMORY_ITEMS)
    return _memory_store


def get_session_manager() -> SessionMemoryManager:
    """Singleton session memory manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionMemoryManager(max_history=settings.MAX_CHAT_HISTORY)
    return _session_manager


def get_task_manager() -> TaskManager:
    """Singleton task manager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def get_llm_service() -> LLMService:
    """Singleton LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            model=settings.MODEL_NAME,
        )
    return _llm_service


def get_tool_executor() -> ToolExecutor:
    """Create tool executor with all registered tools."""
    tools = []
    if settings.ENABLE_FILE_TOOL:
        tools.append(FileTool())
    if settings.ENABLE_WEB_TOOL:
        tools.append(WebTool())
    if settings.ENABLE_SHELL_TOOL:
        tools.append(ShellTool(timeout=settings.SHELL_TIMEOUT))
    return ToolExecutor(tools=tools)
