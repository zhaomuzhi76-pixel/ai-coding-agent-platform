"""AgentSupervisor: 多 agent 进程池。

契约：
  - 按 AgentSpec.agent_id 分组；每组最多 max_per_spec 个
  - 复用空闲；满则等；崩则剔除
  - 支持异构（多 LLM / 多 agent）

不负责：
  - IPC 细节（agent_process 管）
  - 协议（protocol 管）
  - 全局单例（registry 管）
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from .agent_process import AgentProcess, ProcessError
from .spec import AgentSpec

OnStep = Callable[[dict], Any]


class AgentSupervisor:
    VERSION = "1.0"

    def __init__(self, max_per_spec: int = 2) -> None:
        if max_per_spec < 1:
            raise ValueError("max_per_spec must be >= 1")
        self.max_per_spec = int(max_per_spec)
        self._pools: dict[str, list[AgentProcess]] = {}
        self._lock = asyncio.Lock()
        self.spawned_total = 0
        self.reused_total = 0

    async def submit(
        self, spec: AgentSpec, task_msg: dict, on_step: OnStep | None = None,
    ) -> dict:
        proc = await self._acquire(spec)
        try:
            return await proc.submit(task_msg, on_step=on_step)
        except ProcessError:
            await self._drop(spec.agent_id, proc)
            raise

    async def shutdown_all(self) -> None:
        async with self._lock:
            allp = [p for ps in self._pools.values() for p in ps]
            self._pools.clear()
        for p in allp:
            await p.stop()

    def dump(self) -> dict:
        return {
            "name": type(self).__name__, "version": self.VERSION,
            "max_per_spec": self.max_per_spec,
            "agents": {aid: [p.dump() for p in ps]
                       for aid, ps in self._pools.items()},
            "spawned_total": self.spawned_total,
            "reused_total": self.reused_total,
        }

    async def _acquire(self, spec: AgentSpec) -> AgentProcess:
        async with self._lock:
            procs = self._pools.get(spec.agent_id, [])
            procs = [p for p in procs if p.is_alive()]
            for p in procs:
                if not p.busy:
                    self.reused_total += 1
                    self._pools[spec.agent_id] = procs
                    return p
            if len(procs) < self.max_per_spec:
                new = AgentProcess(spec, index=len(procs))
                procs.append(new)
                self._pools[spec.agent_id] = procs
                self.spawned_total += 1
                await new.start()
                return new
            self._pools[spec.agent_id] = procs
        # 等**任一**进程空闲（不是只等 procs[0]）
        # 30s 上限（原 120s 用户感知=卡死）
        for _ in range(300):
            for p in list(procs):
                if p.is_alive() and not p.busy:
                    return p
            await asyncio.sleep(0.1)
        raise ProcessError("no worker available for " + spec.agent_id)

    async def _drop(self, agent_id: str, proc: AgentProcess) -> None:
        async with self._lock:
            procs = self._pools.get(agent_id, [])
            if proc in procs: procs.remove(proc)
            if not procs: self._pools.pop(agent_id, None)
        try: await proc.stop()
        except Exception: pass


__all__ = ["AgentSupervisor"]
