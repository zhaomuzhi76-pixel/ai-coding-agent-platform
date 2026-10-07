"""Turn: 一次用户-LLM 交互（Codex 三级模型第二级）。"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Turn:
    turn_id: str
    thread_id: str
    index: int
    user_message: str
    status: str          # running | done | failed
    started_at: float
    finished_at: float   # 0 = 未完成
    result: dict         # 最终结果（answer/trace）

    @classmethod
    def create(
        cls, thread_id: str, index: int, user_message: str,
    ) -> "Turn":
        return cls(
            turn_id="tn-" + uuid.uuid4().hex[:12],
            thread_id=thread_id,
            index=index,
            user_message=user_message,
            status="running",
            started_at=time.time(),
            finished_at=0.0,
            result={},
        )

    def with_result(self, result: dict) -> "Turn":
        return Turn(
            turn_id=self.turn_id,
            thread_id=self.thread_id,
            index=self.index,
            user_message=self.user_message,
            status="done" if result.get("success") else "failed",
            started_at=self.started_at,
            finished_at=time.time(),
            result=result,
        )

    def to_mongo(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "thread_id": self.thread_id,
            "index": self.index,
            "user_message": self.user_message,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "result": self.result,
        }

    @classmethod
    def from_mongo(cls, doc: dict) -> "Turn":
        return cls(
            turn_id=str(doc["turn_id"]),
            thread_id=str(doc["thread_id"]),
            index=int(doc.get("index", 0)),
            user_message=str(doc.get("user_message", "")),
            status=str(doc.get("status", "running")),
            started_at=float(doc.get("started_at", 0)),
            finished_at=float(doc.get("finished_at", 0)),
            result=dict(doc.get("result", {})),
        )


__all__ = ["Turn"]
