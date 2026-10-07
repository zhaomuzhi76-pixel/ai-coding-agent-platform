"""把 multiplex 底层接入现有 AgentRuntime —— 唯一装配入口。

契约：
  - build_multiplex_runtime(role_specs, max_per_spec=2, router=None)
      → MultiplexTeam
  - MultiplexTeam 持有 AgentRuntime + AgentSupervisor，可直接编排
  - role_specs: [(name, model_chain, workspace?, max_steps?), ...]
  - 内部：构造 supervisor / router / ProcessRole → 注册进 RoleRegistry

不负责：
  - 编排逻辑（现有 AgentRuntime 管）
  - 进程 / 协议（L0/L1 管）
  - 模型健康（调用方注入 router）
"""
from __future__ import annotations

from typing import Any

from backend.agent.runtime.blackboard import Blackboard
from backend.agent.runtime.message import AgentMessage
from backend.agent.runtime.role import RoleRegistry
from backend.agent.runtime.runtime import AgentRuntime

from .model_router import MultiplexModelRouter
from .process_role import ProcessRole
from .supervisor import AgentSupervisor


class MultiplexTeam:
    VERSION = "1.0"

    def __init__(
        self,
        runtime: AgentRuntime,
        supervisor: AgentSupervisor,
        router: MultiplexModelRouter,
        role_names: tuple,
    ) -> None:
        if not isinstance(runtime, AgentRuntime):
            raise TypeError("runtime must be AgentRuntime")
        if not isinstance(supervisor, AgentSupervisor):
            raise TypeError("supervisor must be AgentSupervisor")
        if not isinstance(router, MultiplexModelRouter):
            raise TypeError("router must be MultiplexModelRouter")
        self.runtime = runtime
        self.supervisor = supervisor
        self.router = router
        self.role_names = tuple(role_names)
        if not self.role_names:
            raise ValueError("at least one role required")

    async def run_chain(
        self,
        task: str,
        session_id: str = "",
        metadata: dict | None = None,
    ) -> list:
        """顺序链：每个 role 的输出作为下一个 role 的输入。

        起点 = 第一个注册的 role。
        """
        sid = session_id or "team-" + str(id(self))
        meta = dict(metadata or {})
        meta["session_id"] = sid
        plan = [(name, None) for name in self.role_names]
        return await self.runtime.dispatch_chain(
            plan=plan,
            initial_role=self.role_names[0],
            initial=AgentMessage(
                role="user", content=task, metadata=meta,
            ),
        )

    async def run_parallel(
        self,
        task: str,
        session_id: str = "",
        metadata: dict | None = None,
    ) -> list:
        """并发：所有 role 同时收到同一任务（黑板上共享）。"""
        sid = session_id or "team-" + str(id(self))
        meta = dict(metadata or {})
        meta["session_id"] = sid
        plan = [
            (name, AgentMessage(role="user", content=task, metadata=meta))
            for name in self.role_names
        ]
        return await self.runtime.dispatch_many(plan)

    async def shutdown(self) -> None:
        await self.supervisor.shutdown_all()

    def ready(self) -> bool:
        return (
            self.runtime.ready()
            and self.supervisor is not None
            and self.router is not None
        )

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "roles": list(self.role_names),
            "runtime": self.runtime.dump(),
            "supervisor": self.supervisor.dump(),
            "router": self.router.dump(),
        }


def build_multiplex_runtime(
    role_specs: list,
    *,
    max_per_spec: int = 2,
    router: MultiplexModelRouter | None = None,
    workspace: str = "",
) -> MultiplexTeam:
    """构造一个接到现有 AgentRuntime 的多进程多 agent 编队。

    role_specs 元素：str 或 dict 或 (name, model_chain) 元组
        - str: name，model_chain 必填字段？→ 用 name 当 model
        - dict: {name, model_chain, workspace?, max_steps?}
        - tuple: (name, model_chain)
    """
    if not role_specs:
        raise ValueError("role_specs required")

    supervisor = AgentSupervisor(max_per_spec=max_per_spec)
    router_inst = router or MultiplexModelRouter()
    registry = RoleRegistry()
    names: list[str] = []

    for spec in role_specs:
        if isinstance(spec, str):
            name, chain, ws, ms = spec, ((("", spec),)), workspace, 10
        elif isinstance(spec, dict):
            name = str(spec.get("name", ""))
            chain = tuple(spec.get("model_chain") or ((("", name),),))
            ws = str(spec.get("workspace", workspace))
            ms = int(spec.get("max_steps", 10))
        elif isinstance(spec, (tuple, list)) and len(spec) >= 2:
            name = str(spec[0])
            chain = tuple(spec[1]) if isinstance(spec[1], (tuple, list)) else ((("", spec[1]),),)
            ws = str(spec[2]) if len(spec) > 2 else workspace
            ms = int(spec[3]) if len(spec) > 3 else 10
        else:
            raise TypeError("bad role_spec: " + repr(spec))

        if not name:
            raise ValueError("role name required")
        role = ProcessRole(
            name=name, model_chain=chain, supervisor=supervisor,
            router=router_inst, workspace=ws, max_steps=ms,
        )
        registry.register(role)
        names.append(name)

    runtime = AgentRuntime(registry=registry, blackboard=Blackboard())
    return MultiplexTeam(
        runtime=runtime, supervisor=supervisor,
        router=router_inst, role_names=tuple(names),
    )


__all__ = ["MultiplexTeam", "build_multiplex_runtime"]
