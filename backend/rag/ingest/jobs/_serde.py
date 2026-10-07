"""Job 序列化辅助。职责：IngestJob ↔ dict 互转（含损坏数据容错）。
不做存储、不创建 job。_ 前缀表示内部模块。
"""
from __future__ import annotations
from typing import Optional

from backend.rag.ingest.jobs.contracts import (
    IngestJob, JobPhase, JobProgress, JobStatus)


def deserialize(d: dict) -> Optional[IngestJob]:
    """从 dict 恢复 IngestJob。损坏数据 → 返回 None。
    重启后：PENDING/RUNNING 一律视为 FAILED（中断）。"""
    try:
        p = d.get("progress") or {}
        prog = JobProgress(
            phase=JobPhase(p.get("phase", "queued")),
            current=int(p.get("current", 0)),
            total=int(p.get("total", 0)),
            indexed=int(p.get("indexed", 0)),
            message=str(p.get("message", "")),
        )
        status = JobStatus(d.get("status", "pending"))
        # [RESUME_PENDING] 重启时：
        #   PENDING / RUNNING → PENDING（可被 resume_all 重新入队）
        #   PENDING_REVIEW → PENDING_REVIEW（可自动 approve）
        if status == JobStatus.RUNNING:
            status = JobStatus.PENDING
        # 注意：不再把 PENDING 强杀为 FAILED
        return IngestJob(
            job_id=str(d["job_id"]), filename=str(d["filename"]),
            kb=str(d["kb"]), lang=str(d.get("lang", "")),
            size_bytes=int(d.get("size_bytes", 0)),
            status=status, progress=prog,
            created_at=float(d.get("created_at", 0)),
            started_at=float(d.get("started_at", 0)),
            finished_at=float(d.get("finished_at", 0)),
            error=str(d.get("error", "")) or (
                "interrupted by restart"
                if status == JobStatus.FAILED else ""),
            origin_hash=str(d.get("origin_hash", "")),
            chunks_indexed=int(d.get("chunks_indexed", 0)),
            draft_path=str(d.get("draft_path", "")),
            draft_count=int(d.get("draft_count", 0)),
            meta=dict(d.get("meta") or {}),
        )
    except Exception:
        return None


__all__ = ["deserialize"]
