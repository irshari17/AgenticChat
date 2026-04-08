"""
Agent Registry — tracks active agents, assigns tasks, supports parallel execution.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger("agents.registry")


class AgentInstance:
    """A registered agent instance."""

    def __init__(self, agent_type: str, agent_id: Optional[str] = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.agent_type = agent_type
        self.status = "idle"  # idle, busy, completed, failed
        self.created_at = datetime.utcnow()
        self.current_task_id: Optional[str] = None
        self.completed_tasks: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def assign_task(self, task_id: str):
        self.current_task_id = task_id
        self.status = "busy"

    def complete_task(self):
        if self.current_task_id:
            self.completed_tasks.append(self.current_task_id)
        self.current_task_id = None
        self.status = "idle"

    def fail(self):
        self.current_task_id = None
        self.status = "failed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "completed_tasks_count": len(self.completed_tasks),
        }


class AgentRegistry:
    """
    Registry that tracks all active agents in the system.
    Supports spawning new agent instances and tracking their lifecycle.
    """

    def __init__(self):
        self.agents: Dict[str, AgentInstance] = {}

    def spawn(self, agent_type: str, agent_id: Optional[str] = None) -> AgentInstance:
        """Spawn a new agent instance."""
        instance = AgentInstance(agent_type=agent_type, agent_id=agent_id)
        self.agents[instance.agent_id] = instance
        logger.info(f"Agent spawned: {agent_type} ({instance.agent_id[:8]})")
        return instance

    def get(self, agent_id: str) -> Optional[AgentInstance]:
        return self.agents.get(agent_id)

    def get_by_type(self, agent_type: str) -> List[AgentInstance]:
        return [a for a in self.agents.values() if a.agent_type == agent_type]

    def get_idle(self, agent_type: Optional[str] = None) -> List[AgentInstance]:
        agents = self.agents.values()
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        return [a for a in agents if a.status == "idle"]

    def get_active(self) -> List[AgentInstance]:
        return [a for a in self.agents.values() if a.status == "busy"]

    def remove(self, agent_id: str):
        self.agents.pop(agent_id, None)

    def clear(self):
        self.agents.clear()

    def summary(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for a in self.agents.values():
            types[a.agent_type] = types.get(a.agent_type, 0) + 1
        return {
            "total": len(self.agents),
            "active": len(self.get_active()),
            "by_type": types,
        }
