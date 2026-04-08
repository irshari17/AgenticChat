"""
Shared Memory — accessible by all agents for storing intermediate results,
coordination data, and cross-agent communication.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import logging

logger = logging.getLogger("memory.shared")


class SharedMemoryEntry:
    def __init__(self, key: str, value: Any, source_agent: str = "unknown", ttl: int = 0):
        self.id = str(uuid.uuid4())
        self.key = key
        self.value = value
        self.source_agent = source_agent
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.ttl = ttl  # 0 = never expires
        self.access_count = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl <= 0:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl


class SharedMemory:
    """
    Thread-safe shared memory store for inter-agent communication.
    All agents can read from and write to this store.
    """

    def __init__(self):
        self._store: Dict[str, SharedMemoryEntry] = {}
        self._session_stores: Dict[str, Dict[str, SharedMemoryEntry]] = {}

    def set(self, key: str, value: Any, source_agent: str = "unknown",
            session_id: Optional[str] = None, ttl: int = 0):
        """Store a value. Optionally scoped to a session."""
        entry = SharedMemoryEntry(key=key, value=value, source_agent=source_agent, ttl=ttl)
        store = self._get_store(session_id)
        store[key] = entry
        logger.debug(f"SharedMemory SET: {key}={str(value)[:100]} (agent={source_agent})")

    def get(self, key: str, session_id: Optional[str] = None, default: Any = None) -> Any:
        """Retrieve a value by key."""
        store = self._get_store(session_id)
        entry = store.get(key)
        if entry is None:
            return default
        if entry.is_expired:
            del store[key]
            return default
        entry.access_count += 1
        return entry.value

    def get_all(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all non-expired entries."""
        store = self._get_store(session_id)
        result = {}
        expired_keys = []
        for key, entry in store.items():
            if entry.is_expired:
                expired_keys.append(key)
            else:
                result[key] = entry.value
        for k in expired_keys:
            del store[k]
        return result

    def get_by_agent(self, agent_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all entries set by a specific agent."""
        store = self._get_store(session_id)
        return {
            k: e.value for k, e in store.items()
            if e.source_agent == agent_name and not e.is_expired
        }

    def delete(self, key: str, session_id: Optional[str] = None) -> bool:
        store = self._get_store(session_id)
        if key in store:
            del store[key]
            return True
        return False

    def clear(self, session_id: Optional[str] = None):
        if session_id:
            self._session_stores.pop(session_id, None)
        else:
            self._store.clear()

    def _get_store(self, session_id: Optional[str] = None) -> Dict[str, SharedMemoryEntry]:
        if session_id is None:
            return self._store
        if session_id not in self._session_stores:
            self._session_stores[session_id] = {}
        return self._session_stores[session_id]

    def summary(self, session_id: Optional[str] = None) -> str:
        """Get a text summary of shared memory contents."""
        data = self.get_all(session_id)
        if not data:
            return "Shared memory is empty."
        lines = ["Shared Memory Contents:"]
        for k, v in data.items():
            val_str = str(v)[:200]
            lines.append(f"  [{k}]: {val_str}")
        return "\n".join(lines)
