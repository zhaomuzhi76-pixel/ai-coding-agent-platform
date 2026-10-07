"""Multi-Agent 协作包（L0~L5 完整 6 层）。

层结构：
  L0  agent_registry.py     Agent 注册表
  L1  task_router.py        任务路由
  L2  message_bus.py        Agent 间通信
  L3  graph_executor.py     DAG 编排
  L4  handoff.py            Agent 转交
  L5  shared_memory.py      跨 Agent 共享记忆
"""
from backend.application.multi_agent.agent_registry import (
    AgentRegistry, AgentDescriptor, get_default_registry,
    register_builtin_agents,
)
from backend.application.multi_agent.task_router import (
    TaskRouter, RouteDecision, get_default_router,
)
from backend.application.multi_agent.message_bus import (
    MessageBus, Message, get_default_bus,
)
from backend.application.multi_agent.graph_executor import (
    GraphNode, Graph, GraphExecutor, make_graph,
)
from backend.application.multi_agent.handoff import (
    HandoffRule, HandoffRecord, HandoffManager, get_default_handoff,
)
from backend.application.multi_agent.shared_memory import (
    SharedMemory, get_default_memory,
)

__all__ = [
    "AgentRegistry", "AgentDescriptor", "get_default_registry",
    "register_builtin_agents",
    "TaskRouter", "RouteDecision", "get_default_router",
    "MessageBus", "Message", "get_default_bus",
    "GraphNode", "Graph", "GraphExecutor", "make_graph",
    "HandoffRule", "HandoffRecord", "HandoffManager", "get_default_handoff",
    "SharedMemory", "get_default_memory",
]
