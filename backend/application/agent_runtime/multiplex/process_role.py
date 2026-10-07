"""ProcessRole: 用 AgentProcess 实现现有 AgentRole Protocol。

契约：
  - name = role_id
  - async run(message, blackboard) → AgentMessage（新 output 写回 blackboard）
  - ready() = 依赖就绪
  - 与 backend/agent/runtime/role.AgentRole Protocol 兼容（isinstance 通过）

不负责：
  - 进程管理（supervisor 管）
  - 协议（protocol 管）
  - Blackboard 结构（抽象层定义）
"""
from __future__ import annotations

from typing import Any

from backend.agent.runtime.blackboard import Blackboard
from backend.agent.runtime.message import AgentMessage

from . import protocol
from .model_router import MultiplexModelRouter
from .spec import AgentSpec
from .supervisor import AgentSupervisor


class ProcessRole:
    VERSION = "1.0"

    def __init__(
        self,
        name: str,
        model_chain,
        supervisor: AgentSupervisor,
        router: MultiplexModelRouter | None = None,
        workspace: str = "",
        max_steps: int = 10,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("ProcessRole.name required")
        if not isinstance(supervisor, AgentSupervisor):
            raise TypeError("supervisor must be AgentSupervisor")
        self.name = name.strip()
        self.model_chain = tuple(model_chain or ())
        if not self.model_chain:
            raise ValueError("ProcessRole.model_chain required")
        self.supervisor = supervisor
        self.router = router or MultiplexModelRouter()
        self.workspace = str(workspace)
        self.max_steps = int(max_steps)
        self.runs = 0
        self.failures = 0

    async def run(
        self, message: AgentMessage, blackboard: Blackboard,
    ) -> AgentMessage:
        if not isinstance(blackboard, Blackboard):
            raise TypeError("blackboard must be Blackboard")
        self.runs += 1
        session_id = str(getattr(message, "session_id", "") or "") or (
            "role-" + self.name
        )
        content = str(getattr(message, "content", "") or "")

        try:
            provider, model = self.router.route(self.model_chain)
        except Exception as exc:
            self.failures += 1
            return AgentMessage(
                role=self.name,
                content="[route failed] " + type(exc).__name__ + ": " + str(exc),
            )

        spec = AgentSpec(
            agent_id=self.name, provider=provider, model=model,
            workspace=self.workspace, max_steps=self.max_steps,
        )
        task_id = "role-" + self.name + "-" + session_id[-6:]
        task_msg = protocol.make_task(
            session_id=session_id, task_id=task_id,
            message=content, workspace=self.workspace,
            provider=provider, model=model, max_steps=self.max_steps,
        )

        try:
            resp = await self.supervisor.submit(spec, task_msg)
        except Exception as exc:
            self.failures += 1
            return AgentMessage(
                role=self.name,
                content="[submit failed] " + type(exc).__name__ + ": " + str(exc),
            )

        mtype = resp.get("type")
        if mtype == protocol.MSG_RESULT:
            out = resp.get("result")
            blackboard.set(self.name + ".output", out)
            blackboard.set(self.name + ".model", model)
            return AgentMessage(
                role=self.name,
                content=str(out) if out is not None else "",
            )
        self.failures += 1
        err = str(resp.get("error", "unknown"))
        return AgentMessage(role=self.name, content="[error] " + err)

    def ready(self) -> bool:
        return (
            self.supervisor is not None
            and self.router is not None
            and bool(self.model_chain)
        )

    def dump(self) -> dict:
        return {
            "name": self.name, "version": self.VERSION,
            "model_chain": [list(m) if isinstance(m, (tuple, list)) else m
                            for m in self.model_chain],
            "runs": self.runs, "failures": self.failures,
            "ready": self.ready(),
        }


__all__ = ["ProcessRole"]
