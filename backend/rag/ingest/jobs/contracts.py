"""异步采集任务契约。职责：只描述任务状态、进度、快照。
不做调度（worker 管）、不存储（registry 管）、不做解析（ingest.service 管）。
与 rag/ingest/contracts 边界：
  那层管"单次采集报告"；本层管"长时任务的完整生命周期"。
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional


class JobStatus(str, Enum):
    PENDING = "pending"             # 已入队
    RUNNING = "running"             # 处理中
    PENDING_REVIEW = "pending_review"  # 待审核（已解析未入库）
    DONE = "done"                   # 完成（已入库）
    FAILED = "failed"               # 失败
    CANCELLED = "cancelled"         # 用户取消
    REJECTED = "rejected"           # 用户拒绝入库


class JobPhase(str, Enum):
    QUEUED = "queued"         # 等待启动
    UPLOADING = "uploading"   # 接收文件
    SAVING = "saving"         # 保存原件
    PARSING = "parsing"       # 解析/OCR
    CHUNKING = "chunking"     # 切块
    EMBEDDING = "embedding"   # 向量化
    INDEXING = "indexing"     # 写库
    FINALIZING = "finalizing" # 汇总
    COMPLETED = "completed"
    ERROR = "error"


def _freeze(m: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(m))


def new_job_id() -> str:
    return "job-" + uuid.uuid4().hex[:16]


@dataclass(frozen=True)
class JobProgress:
    phase: JobPhase = JobPhase.QUEUED
    current: int = 0          # 已处理单元（如已 OCR 页数）
    total: int = 0            # 总单元（0 = 未知）
    indexed: int = 0          # 已索引块数
    message: str = ""

    def __post_init__(self) -> None:
        if self.current < 0 or self.total < 0 or self.indexed < 0:
            raise ValueError("progress 数值不能为负")

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(1.0, self.current / self.total)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "current": self.current,
            "total": self.total,
            "indexed": self.indexed,
            "percent": round(self.percent, 4),
            "message": self.message,
        }


@dataclass(frozen=True)
class JobStep:
    """单个执行步骤。用于追踪整个过程。"""
    ts: float
    phase: JobPhase
    message: str = ""
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", _freeze(self.detail))

    def to_dict(self) -> dict:
        return {"ts": self.ts, "phase": self.phase.value,
                "message": self.message, "detail": dict(self.detail)}


@dataclass(frozen=True)
class IngestJob:
    job_id: str
    filename: str
    kb: str
    lang: str = ""
    size_bytes: int = 0
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = field(default_factory=JobProgress)
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    finished_at: float = 0.0
    error: str = ""
    origin_hash: str = ""
    chunks_indexed: int = 0
    draft_path: str = ""
    draft_count: int = 0
    meta: Mapping[str, Any] = field(default_factory=dict)
    steps: Tuple[JobStep, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze(self.meta))
        if not isinstance(self.steps, tuple):
            raise TypeError("steps must be tuple")
        if not self.job_id: raise ValueError("job_id required")
        if not self.filename: raise ValueError("filename required")
        if self.size_bytes < 0: raise ValueError("size_bytes must be >= 0")

    @property
    def elapsed_ms(self) -> int:
        end = self.finished_at or time.time()
        start = self.started_at or self.created_at
        return int((end - start) * 1000)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "kb": self.kb,
            "lang": self.lang,
            "size_bytes": self.size_bytes,
            "status": self.status.value,
            "progress": self.progress.to_dict(),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
            "origin_hash": self.origin_hash,
            "chunks_indexed": self.chunks_indexed,
            "draft_path": self.draft_path,
            "draft_count": self.draft_count,
            "meta": dict(self.meta),
            "steps": [st.to_dict() for st in self.steps],
        }

    def with_progress(self, p: JobProgress,
                      status: Optional[JobStatus] = None) -> "IngestJob":
        """返回新实例（frozen 友好）。"""
        return IngestJob(
            job_id=self.job_id, filename=self.filename,
            kb=self.kb, lang=self.lang, size_bytes=self.size_bytes,
            status=status or self.status, progress=p,
            created_at=self.created_at, started_at=self.started_at,
            finished_at=self.finished_at, error=self.error,
            origin_hash=self.origin_hash,
            chunks_indexed=self.chunks_indexed, meta=self.meta,
            steps=self.steps, draft_path=self.draft_path,
            draft_count=self.draft_count,
        )

    def with_draft(self, path: str, count: int) -> "IngestJob":
        return IngestJob(
            job_id=self.job_id, filename=self.filename,
            kb=self.kb, lang=self.lang, size_bytes=self.size_bytes,
            status=JobStatus.PENDING_REVIEW, progress=self.progress,
            created_at=self.created_at, started_at=self.started_at,
            finished_at=time.time(), error=self.error,
            origin_hash=self.origin_hash,
            chunks_indexed=0,
            draft_path=path, draft_count=count,
            meta=self.meta, steps=self.steps,
        )

    def with_status(self, status: JobStatus, *,
                    error: str = "",
                    origin_hash: Optional[str] = None,
                    chunks_indexed: Optional[int] = None
                    ) -> "IngestJob":
        return IngestJob(
            job_id=self.job_id, filename=self.filename,
            kb=self.kb, lang=self.lang, size_bytes=self.size_bytes,
            status=status, progress=self.progress,
            created_at=self.created_at,
            started_at=self.started_at or (
                time.time() if status == JobStatus.RUNNING else 0.0),
            finished_at=(time.time() if status in (
                JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED)
                else self.finished_at),
            error=error or self.error,
            origin_hash=origin_hash or self.origin_hash,
            chunks_indexed=(chunks_indexed if chunks_indexed is not None
                            else self.chunks_indexed),
            meta=self.meta, steps=self.steps,
            draft_path=self.draft_path,
            draft_count=self.draft_count,
        )


__all__ = ["JobStatus", "JobPhase", "JobStep", "IngestJob",
           "JobProgress", "new_job_id"]
