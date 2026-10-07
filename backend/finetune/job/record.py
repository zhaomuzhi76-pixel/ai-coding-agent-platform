"""训练任务记录（L1 · 聚合数据）。

JobRecord = JobSpec + JobState + 时间戳 + 进度 + 错误。

职责：
    - 聚合任务运行期所有字段
    - 序列化 / 反序列化
    - 供 store 存 / manager 查

不负责：
    - 状态转移（state 管）
    - 持久化（store 管）
    - 执行（runner 管）
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .spec import JobSpec
from .state import JobState


def _new_job_id() -> str:
    return "job-" + uuid.uuid4().hex[:12]


@dataclass
class JobRecord:
    job_id: str
    spec: JobSpec
    state: JobState = JobState.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    finished_at: float = 0.0
    progress: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    saved_to: str = ""
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.job_id:
            self.job_id = _new_job_id()
        if not isinstance(self.spec, JobSpec):
            raise TypeError("JobRecord.spec must JobSpec")
        if not isinstance(self.state, JobState):
            raise TypeError("JobRecord.state must JobState")

    def touch(self) -> None:
        self.updated_at = time.time()

    @property
    def elapsed_sec(self) -> float:
        if self.started_at <= 0:
            return 0.0
        end = self.finished_at if self.finished_at > 0 else time.time()
        return round(end - self.started_at, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "spec": self.spec.to_dict(),
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": round(self.progress, 2),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "loss": float(self.loss),
            "saved_to": self.saved_to,
            "error": self.error,
            "elapsed_sec": self.elapsed_sec,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "JobRecord":
        if not isinstance(d, dict):
            raise TypeError("JobRecord.from_dict expects dict")
        spec_d = d.get("spec")
        if not isinstance(spec_d, dict):
            raise ValueError("JobRecord.spec missing")
        try:
            state = JobState(str(d.get("state", "pending")))
        except ValueError:
            state = JobState.FAILED
        return cls(
            job_id=str(d.get("job_id", "")) or _new_job_id(),
            spec=JobSpec.from_dict(spec_d),
            state=state,
            created_at=float(d.get("created_at", time.time())),
            updated_at=float(d.get("updated_at", time.time())),
            started_at=float(d.get("started_at", 0.0)),
            finished_at=float(d.get("finished_at", 0.0)),
            progress=float(d.get("progress", 0.0)),
            current_step=int(d.get("current_step", 0)),
            total_steps=int(d.get("total_steps", 0)),
            loss=float(d.get("loss", 0.0)),
            saved_to=str(d.get("saved_to", "")),
            error=str(d.get("error", "")),
            metadata=dict(d.get("metadata") or {}),
        )


def create_job_record(spec: JobSpec) -> JobRecord:
    return JobRecord(job_id=_new_job_id(), spec=spec)


__all__ = ["JobRecord", "create_job_record"]
