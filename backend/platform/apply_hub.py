"""ApplyHub: 平台 apply 任务的实时进度 Hub（L1 · pub/sub）。

与 finetune.deploy_hub 的区别（不重复职责）：
    - deploy_hub  管理"模型部署"任务（adapter_id 维度）
    - apply_hub   管理"代码应用"任务（proposal_id 维度）

事件类型：
    step    · 每 chunk 开始/完成
    log     · 过程日志
    result  · 最终汇总
    _end    · 流终止信号（内含 status）
    error   · 异常

不负责：
    - apply 执行（batch_executor 管）
    - 决策（approval_gate 管）
    - WebSocket（apply_ws 管）
"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

_MAX_EVENTS = 2000


class ApplyHub:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}
        self._subs: dict[str, list[asyncio.Queue]] = {}

    def create(self, proposal_id: str) -> str:
        tid = "apply-" + uuid.uuid4().hex[:12]
        self._tasks[tid] = {
            "task_id": tid,
            "proposal_id": proposal_id,
            "status": "pending",
            "created_at": time.time(),
            "events": [],
            "result": None,
        }
        return tid

    def publish(self, tid: str, event: dict) -> None:
        t = self._tasks.get(tid)
        if t is None:
            return
        t["events"].append(event)
        if len(t["events"]) > _MAX_EVENTS:
            t["events"] = t["events"][-_MAX_EVENTS:]
        for q in list(self._subs.get(tid, [])):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self, tid: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=4000)
        self._subs.setdefault(tid, []).append(q)
        return q

    def unsubscribe(self, tid: str, q: asyncio.Queue) -> None:
        try:
            self._subs.get(tid, []).remove(q)
        except ValueError:
            pass

    def finish(self, tid: str, status: str, result: dict | None = None) -> None:
        t = self._tasks.get(tid)
        if t is None:
            return
        t["status"] = status
        t["result"] = result
        self.publish(tid, {"type": "_end", "status": status})

    def get(self, tid: str) -> dict | None:
        return self._tasks.get(tid)

    def list_active(self) -> list[dict]:
        return [
            {"task_id": t["task_id"], "proposal_id": t["proposal_id"],
             "status": t["status"], "created_at": t["created_at"]}
            for t in self._tasks.values()
            if t["status"] not in ("succeeded", "failed", "cancelled")
        ]

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "tasks": len(self._tasks),
            "active": len(self.list_active()),
        }


_hub: ApplyHub | None = None


def get_apply_hub() -> ApplyHub:
    global _hub
    if _hub is None:
        _hub = ApplyHub()
    return _hub


__all__ = ["ApplyHub", "get_apply_hub"]
