"""Thread: 一个会话级任务（Codex 三级模型第一级）。

状态机：
    pending → running → (waiting_approval) → done | failed

持久化：MongoDB agent_threads 集合
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass


STATUSES = frozenset({
    "pending", "running", "waiting_approval",
    "done", "failed", "orphaned",
})


@dataclass(frozen=True, slots=True)
class Thread:
    thread_id: str
    session_id: str
    workspace: str
    status: str
    created_at: float
    updated_at: float
    current_turn: int
    worker_pid: int

    @classmethod
    def create(cls, session_id: str, workspace: str) -> "Thread":
        now = time.time()
        return cls(
            thread_id="th-" + uuid.uuid4().hex[:12],
            session_id=session_id,
            workspace=workspace,
            status="pending",
            created_at=now,
            updated_at=now,
            current_turn=0,
            worker_pid=0,
        )

    def with_status(self, status: str, worker_pid: int = 0) -> "Thread":
        if status not in STATUSES:
            raise ValueError(f"unknown status: {status}")
        return Thread(
            thread_id=self.thread_id,
            session_id=self.session_id,
            workspace=self.workspace,
            status=status,
            created_at=self.created_at,
            updated_at=time.time(),
            current_turn=self.current_turn,
            worker_pid=worker_pid or self.worker_pid,
        )

    def next_turn(self) -> "Thread":
        return Thread(
            thread_id=self.thread_id,
            session_id=self.session_id,
            workspace=self.workspace,
            status=self.status,
            created_at=self.created_at,
            updated_at=time.time(),
            current_turn=self.current_turn + 1,
            worker_pid=self.worker_pid,
        )

    def to_mongo(self) -> dict:
        return {
            "thread_id": self.thread_id,
            "session_id": self.session_id,
            "workspace": self.workspace,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_turn": self.current_turn,
            "worker_pid": self.worker_pid,
        }

    @classmethod
    def from_mongo(cls, doc: dict) -> "Thread":
        return cls(
            thread_id=str(doc["thread_id"]),
            session_id=str(doc["session_id"]),
            workspace=str(doc["workspace"]),
            status=str(doc.get("status", "pending")),
            created_at=float(doc.get("created_at", 0)),
            updated_at=float(doc.get("updated_at", 0)),
            current_turn=int(doc.get("current_turn", 0)),
            worker_pid=int(doc.get("worker_pid", 0)),
        )


__all__ = ["Thread", "STATUSES"]
