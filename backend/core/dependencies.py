"""
Dependency injection — provides singleton service instances.
"""

import logging
from memory.memory_store import MemoryStore
from memory.session_memory import SessionMemoryManager
from memory.shared_memory import SharedMemory
from tasks.task_manager import TaskManager
from services.llm import LLMService
from services.tool_executor import ToolExecutor
from agents.agent_registry import AgentRegistry
from tools.file_tool import FileTool
from tools.web_tool import WebTool
from tools.shell_tool import ShellTool
from core.config import settings

logger = logging.getLogger("dependencies")

# Module-level singletons
_memory_store: MemoryStore = None
_session_manager: SessionMemoryManager = None
_shared_memory: SharedMemory = None
_task_manager: TaskManager = None
_llm_service: LLMService = None
_agent_registry: AgentRegistry = None


def get_memory_store() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore(max_items=settings.MAX_MEMORY_ITEMS)
        logger.info("MemoryStore initialized")
    return _memory_store


def get_session_manager() -> SessionMemoryManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionMemoryManager(max_history=settings.MAX_CHAT_HISTORY)
        logger.info("SessionMemoryManager initialized")
    return _session_manager


def get_shared_memory() -> SharedMemory:
    global _shared_memory
    if _shared_memory is None:
        _shared_memory = SharedMemory()
        logger.info("SharedMemory initialized")
    return _shared_memory


def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
        logger.info("TaskManager initialized")
    return _task_manager


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            model=settings.MODEL_NAME,
            max_retries=settings.MAX_RETRIES,
        )
        logger.info(f"LLMService initialized with model: {settings.MODEL_NAME}")
    return _llm_service


def get_agent_registry() -> AgentRegistry:
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
        logger.info("AgentRegistry initialized")
    return _agent_registry


def get_tool_executor() -> ToolExecutor:
    """Create a fresh tool executor with all enabled tools."""
    tools = []
    if settings.ENABLE_FILE_TOOL:
        tools.append(FileTool())
    if settings.ENABLE_WEB_TOOL:
        tools.append(WebTool())
    if settings.ENABLE_SHELL_TOOL:
        tools.append(ShellTool(timeout=settings.SHELL_TIMEOUT))
    return ToolExecutor(tools=tools)
