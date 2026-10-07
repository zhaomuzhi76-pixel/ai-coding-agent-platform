"""L0 · Agent 注册表（单一职责：Agent 元数据 + 查询）。

职责：
  · register / get / list_all / find_by_capability / find_by_role
  · register_builtin_agents() 注册内置 5 Agent
不做：路由、消息、执行。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class AgentDescriptor:
    agent_id: str
    name: str
    role: str
    capabilities: Tuple[str, ...]
    entry: str = ""
    description: str = ""
    priority: int = 50
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_cap(self, cap: str) -> bool:
        return cap in self.capabilities


class AgentRegistry:
    """线程安全 Agent 注册表。"""

    def __init__(self) -> None:
        self._agents: Dict[str, AgentDescriptor] = {}
        self._lock = RLock()

    def register(self, desc: AgentDescriptor) -> None:
        if not desc.agent_id:
            raise ValueError("agent_id required")
        with self._lock:
            self._agents[desc.agent_id] = desc

    def unregister(self, agent_id: str) -> bool:
        with self._lock:
            return self._agents.pop(agent_id, None) is not None

    def get(self, agent_id: str) -> Optional[AgentDescriptor]:
        with self._lock:
            return self._agents.get(agent_id)

    def list_all(self) -> List[AgentDescriptor]:
        with self._lock:
            return list(self._agents.values())

    def find_by_capability(self, cap: str) -> List[AgentDescriptor]:
        with self._lock:
            out = [a for a in self._agents.values() if a.has_cap(cap)]
        return sorted(out, key=lambda a: a.priority)

    def find_by_role(self, role: str) -> List[AgentDescriptor]:
        with self._lock:
            return [a for a in self._agents.values() if a.role == role]

    def count(self) -> int:
        with self._lock:
            return len(self._agents)

    def dump(self) -> Dict[str, Any]:
        return {
            "count": self.count(),
            "agents": [
                {"id": a.agent_id, "role": a.role,
                 "caps": list(a.capabilities), "priority": a.priority}
                for a in self.list_all()
            ],
        }


_BUILTIN: Tuple[AgentDescriptor, ...] = (
    AgentDescriptor(
        agent_id="planner", name="规划 Agent", role="planner",
        capabilities=("planning", "task_decomposition",
                      "intent_classification"),
        entry="backend.agent.orchestration.planner_agent",
        description="拆解复杂任务、输出执行计划", priority=10,
    ),
    AgentDescriptor(
        agent_id="coder", name="编码 Agent", role="coder",
        capabilities=("code_edit", "code_generate", "code_modify",
                      "file_write", "file_read"),
        entry="backend.agent.orchestration.coder_agent",
        description="代码生成 / 修改 / 文件操作", priority=20,
    ),
    AgentDescriptor(
        agent_id="reviewer", name="审核 Agent", role="reviewer",
        capabilities=("code_review", "quality_check", "approval"),
        entry="backend.agent.orchestration.reviewer_agent",
        description="审核代码/变更、质量把关", priority=30,
    ),
    AgentDescriptor(
        agent_id="rag_qa", name="RAG 问答 Agent", role="rag",
        capabilities=("knowledge_qa", "tcm_lookup", "image_search",
                      "domain_lookup"),
        entry="backend.agent_tools.chat_loop",
        description="多领域知识问答 + 图片检索", priority=40,
    ),
    AgentDescriptor(
        agent_id="chat", name="通用对话 Agent", role="chat",
        capabilities=("chat", "general_qa"),
        entry="backend.agent_tools.chat_loop",
        description="通用对话", priority=90,
    ),
)


def register_builtin_agents(registry: AgentRegistry) -> int:
    n = 0
    for d in _BUILTIN:
        if registry.get(d.agent_id) is None:
            registry.register(d)
            n += 1
    return n


_DEFAULT: Optional[AgentRegistry] = None


def get_default_registry() -> AgentRegistry:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = AgentRegistry()
        register_builtin_agents(_DEFAULT)
    return _DEFAULT


__all__ = [
    "AgentRegistry", "AgentDescriptor",
    "register_builtin_agents", "get_default_registry",
]
