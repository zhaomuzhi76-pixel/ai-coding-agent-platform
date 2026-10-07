"""AgentProcess: 单进程封装（spawn / submit / stop）。

契约：
  - 一个 AgentProcess 绑定一个 AgentSpec（异构支持）
  - spawn：python -m ...multiplex.worker_entry
  - submit：写 task，逐行读 stdout，step 回调 / result 终止
  - 崩溃自动检测；stop 优雅 → 超时 → kill

不负责：
  - 路由（supervisor 管）
  - 协议（protocol 管）
  - 多实例管理（supervisor 管）
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Callable

from . import protocol
from .spec import AgentSpec

_START_TIMEOUT = 15.0
_TASK_TIMEOUT = 600.0
_STOP_TIMEOUT = 5.0
_KILL_TIMEOUT = 3.0

OnStep = Callable[[dict], Any]


class ProcessError(RuntimeError):
    """子进程管理错误。"""


class AgentProcess:
    VERSION = "1.0"

    def __init__(self, spec: AgentSpec, index: int = 0) -> None:
        if not isinstance(spec, AgentSpec):
            raise TypeError("spec must be AgentSpec")
        self.spec = spec
        self.index = int(index)
        self.proc: asyncio.subprocess.Process | None = None
        self.worker_id = ""
        self.busy = False
        self.tasks_done = 0
        self.tasks_failed = 0

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    async def start(self) -> str:
        if self.is_alive():
            return self.worker_id
        env = os.environ.copy()
        env.update(self.spec.to_env())

        self.proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m",
            "backend.application.agent_runtime.multiplex.worker_entry",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=os.getcwd(),
        )
        ready = await asyncio.wait_for(
            self._read_one_until(protocol.MSG_READY),
            timeout=_START_TIMEOUT,
        )
        self.worker_id = str(ready.get("worker_id", ""))
        return self.worker_id

    async def submit(
        self,
        task_msg: dict,
        on_step: OnStep | None = None,
        timeout: float = _TASK_TIMEOUT,
    ) -> dict:
        if not self.is_alive():
            raise ProcessError("process not alive")
        if self.busy:
            raise ProcessError("process busy")
        self.busy = True
        try:
            self._write(task_msg)
            return await asyncio.wait_for(
                self._read_until_terminal(on_step),
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            self.tasks_failed += 1
            raise ProcessError("task timeout") from exc
        finally:
            self.busy = False

    async def stop(self) -> None:
        if self.proc is None:
            return
        if self.proc.returncode is not None:
            self.proc = None
            return
        try:
            self._write(protocol.make_shutdown())
            await asyncio.wait_for(self.proc.wait(), timeout=_STOP_TIMEOUT)
        except Exception:
            try:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=_KILL_TIMEOUT)
            except Exception:
                try: self.proc.kill()
                except Exception: pass
        self.proc = None

    def dump(self) -> dict:
        return {
            "name": type(self).__name__, "version": self.VERSION,
            "agent_id": self.spec.agent_id,
            "provider": self.spec.provider, "model": self.spec.model,
            "worker_id": self.worker_id,
            "pid": self.proc.pid if self.proc else 0,
            "busy": self.busy, "alive": self.is_alive(),
            "tasks_done": self.tasks_done, "tasks_failed": self.tasks_failed,
        }

    # ── 内部 ──
    def _write(self, msg: dict) -> None:
        if self.proc is None or self.proc.stdin is None:
            raise ProcessError("stdin unavailable")
        self.proc.stdin.write(protocol.encode_message(msg))

    async def _read_one_until(self, target: str) -> dict:
        if self.proc is None or self.proc.stdout is None:
            raise ProcessError("stdout unavailable")
        while True:
            line = await self.proc.stdout.readline()
            if not line:
                raise ProcessError("process exited")
            try: msg = protocol.decode_message(line)
            except protocol.ProtocolError: continue
            if msg is None: continue
            if msg.get("type") == target:
                return msg

    async def _read_until_terminal(self, on_step: OnStep | None) -> dict:
        if self.proc is None or self.proc.stdout is None:
            raise ProcessError("stdout unavailable")
        while True:
            line = await self.proc.stdout.readline()
            if not line:
                self.tasks_failed += 1
                raise ProcessError("process exited")
            try: msg = protocol.decode_message(line)
            except protocol.ProtocolError: continue
            if msg is None: continue
            mtype = msg.get("type")
            if mtype == protocol.MSG_STEP:
                if on_step is not None:
                    try:
                        r = on_step(msg.get("entry") or {})
                        if asyncio.iscoroutine(r): await r
                    except Exception: pass
                continue
            if mtype in (protocol.MSG_RESULT, protocol.MSG_ERROR):
                if mtype == protocol.MSG_RESULT: self.tasks_done += 1
                else: self.tasks_failed += 1
                return msg
            if mtype == protocol.MSG_PING:
                self._write(protocol.make_pong())
                continue


__all__ = ["AgentProcess", "ProcessError"]
