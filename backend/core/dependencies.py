"""
Dependency injection for FastAPI routes.
Provides shared instances of services, memory, and task manager.
"""

from functools import lru_cache

from memory.memory_store import MemoryStore
from memory.session_memory import SessionMemoryManager
from tasks.task_manager import TaskManager
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from tools.file_tool import FileTool
from tools.web_tool import WebTool
from tools.shell_tool import ShellTool
from core.config import settings


@lru_cache()
def get_memory_store() -> MemoryStore:
    """Singleton memory store instance."""
    return MemoryStore(max_items=settings.MAX_MEMORY_ITEMS)


@lru_cache()
def get_session_manager() -> SessionMemoryManager:
    """Singleton session memory manager."""
    return SessionMemoryManager(max_history=settings.MAX_CHAT_HISTORY)


@lru_cache()
def get_task_manager() -> TaskManager:
    """Singleton task manager."""
    return TaskManager()


@lru_cache()
def get_llm_service() -> LLMService:
    """Singleton LLM service."""
    return LLMService(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        model=settings.MODEL_NAME,
    )


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
