"""Unified agent runtime: messages, blackboard, roles.

冻结层复用：
    agent.graph.task_graph -> TaskGraph (DAG 容器)
    agent.orchestration.contracts -> EditContext / RoleResult

本包只提供通用容器能力，不重复 DAG 容器、不重复 Agent 实现。
"""
from backend.agent.runtime.message import AgentMessage
from backend.agent.runtime.blackboard import Blackboard
from backend.agent.runtime.role import AgentRole, RoleRegistry
from backend.agent.runtime.runtime import AgentRuntime

__all__ = [
    "AgentMessage",
    "Blackboard",
    "AgentRole",
    "RoleRegistry",
    "AgentRuntime",
]
