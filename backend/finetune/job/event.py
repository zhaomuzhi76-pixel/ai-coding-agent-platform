"""任务进度事件（L0 · 纯数据）。

职责：
    - 定义 JobEvent（任务生命周期中的每一步）
    - 事件构造工厂
    - 序列化

不负责：
    - 状态机（state 管）
    - 持久化（store 管）
    - 推送（未来 WS / SSE）

事件类型：
    created    · 任务已创建（pending）
    started    · 开始执行（pending → running）
    progress   · 训练进度（step / loss / lr）
    log        · 日志输出
    epoch      · 一个 epoch 结束
    checkpoint · 保存检查点
    eval       · 评估指标
    succeeded  · 成功结束（→ succeeded）
    failed     · 失败结束（→ failed）
    cancelled  · 用户取消（→ cancelled）
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

_EVENT_TYPES = frozenset({
    "created", "started", "progress", "log", "epoch",
    "checkpoint", "eval", "succeeded", "failed", "cancelled",
})


@dataclass(frozen=True, slots=True)
class JobEvent:
    event_type: str
    payload: dict
    created_at: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self) -> None:
        if self.event_type not in _EVENT_TYPES:
            raise ValueError(f"unknown event_type: {self.event_type}")
        if not isinstance(self.payload, dict):
            raise TypeError("JobEvent.payload must be dict")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "JobEvent":
        if not isinstance(d, dict):
            raise TypeError("JobEvent.from_dict expects dict")
        return cls(
            event_type=str(d.get("event_type", "log")),
            payload=dict(d.get("payload") or {}),
            created_at=float(d.get("created_at", time.time())),
            event_id=str(d.get("event_id") or uuid.uuid4().hex[:12]),
        )


def make_event(event_type: str, **payload: Any) -> JobEvent:
    """快捷构造。"""
    return JobEvent(event_type=event_type, payload=dict(payload))


def created_event(job_id: str, spec: dict) -> JobEvent:
    return JobEvent("created", {"job_id": job_id, "spec": spec})


def started_event(job_id: str) -> JobEvent:
    return JobEvent("started", {"job_id": job_id})


def progress_event(job_id: str, step: int, total: int,
                   loss: float = 0.0, lr: float = 0.0,
                   **extra: Any) -> JobEvent:
    pct = round(step / total * 100.0, 2) if total > 0 else 0.0
    return JobEvent("progress", {
        "job_id": job_id, "step": step, "total": total,
        "percent": pct, "loss": float(loss), "lr": float(lr),
        **extra,
    })


def log_event(job_id: str, message: str, level: str = "info") -> JobEvent:
    return JobEvent("log", {"job_id": job_id, "message": message, "level": level})


def epoch_event(job_id: str, epoch: int, total_epochs: int,
                **metrics: Any) -> JobEvent:
    return JobEvent("epoch", {
        "job_id": job_id, "epoch": epoch,
        "total_epochs": total_epochs, "metrics": dict(metrics),
    })


def checkpoint_event(job_id: str, path: str, step: int) -> JobEvent:
    return JobEvent("checkpoint", {"job_id": job_id, "path": path, "step": step})


def eval_event(job_id: str, metrics: dict) -> JobEvent:
    return JobEvent("eval", {"job_id": job_id, "metrics": dict(metrics)})


def succeeded_event(job_id: str, saved_to: str = "", **extra: Any) -> JobEvent:
    return JobEvent("succeeded", {"job_id": job_id, "saved_to": saved_to, **extra})


def failed_event(job_id: str, error: str) -> JobEvent:
    return JobEvent("failed", {"job_id": job_id, "error": error})


def cancelled_event(job_id: str, reason: str = "user cancelled") -> JobEvent:
    return JobEvent("cancelled", {"job_id": job_id, "reason": reason})


__all__ = [
    "JobEvent",
    "make_event",
    "created_event", "started_event", "progress_event",
    "log_event", "epoch_event", "checkpoint_event", "eval_event",
    "succeeded_event", "failed_event", "cancelled_event",
]
