"""部署任务实时进度 Hub（进程内 pub/sub + task 表）。"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

_MAX_EVENTS = 500


class DeployHub:
    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}
        self._subs: dict[str, list[asyncio.Queue]] = {}

    def create(self, adapter_id: str) -> str:
        tid = "deploy-" + uuid.uuid4().hex[:12]
        self._tasks[tid] = {
            "task_id": tid,
            "adapter_id": adapter_id,
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
        q: asyncio.Queue = asyncio.Queue(maxsize=2000)
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


_hub: DeployHub | None = None


def get_deploy_hub() -> DeployHub:
    global _hub
    if _hub is None:
        _hub = DeployHub()
    return _hub


__all__ = ["DeployHub", "get_deploy_hub"]
