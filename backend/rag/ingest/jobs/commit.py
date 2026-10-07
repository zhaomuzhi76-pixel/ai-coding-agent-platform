"""入库提交。职责：把已审核的草稿块索引进向量库。
不解析（service 管）、不存草稿（draft_store 管）、不检索（preview 管）。
边界：审核门打开后，用户通过 commit/reject 决定入库与否。
"""
from __future__ import annotations
from typing import Any, Optional, Sequence

from backend.rag.ingest.jobs.contracts import JobStatus
from backend.rag.ingest.jobs.draft_store import (
    DraftStore, get_default_draft_store)
from backend.rag.ingest.jobs.registry import (
    JobRegistry, get_default_job_registry)
from backend.rag.multimodal.contracts import ImageRef, MultimodalChunk

BATCH = 64


def _to_chunk(dc) -> MultimodalChunk:
    imgs = tuple(ImageRef.from_dict(i) for i in dc.images) if dc.images else ()
    return MultimodalChunk(
        chunk_id=dc.chunk_id, text=dc.text, images=imgs,
        source=dc.source, source_path=dc.source_path,
        line_no=dc.line_no, role=dc.role, metadata=dc.metadata)


class JobCommitter:
    def __init__(self, *, indexer: Any,
                 registry: Optional[JobRegistry] = None,
                 draft_store: Optional[DraftStore] = None) -> None:
        if indexer is None: raise ValueError("indexer required")
        self._ix = indexer
        self._reg = registry or get_default_job_registry()
        self._drafts = draft_store or get_default_draft_store()

    def commit(self, job_id: str, *,
               keep_ids: Optional[Sequence[str]] = None) -> dict:
        """确认入库。keep_ids=None 表示全部；[] 表示全部丢弃。"""
        job = self._reg.get(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        drafts = self._drafts.read(job_id)
        if not drafts:
            raise ValueError(f"no drafts: {job_id}")
        if keep_ids is not None:
            keep = set(str(x) for x in keep_ids)
            drafts = [d for d in drafts if d.chunk_id in keep]
        if not drafts:
            self._drafts.delete(job_id)
            self._reg.finish(job_id, status=JobStatus.REJECTED,
                              error="user rejected all chunks",
                              origin_hash=job.origin_hash,
                              chunks_indexed=0)
            return {"job_id": job_id, "committed": 0, "status": "rejected"}
        chunks = [_to_chunk(d) for d in drafts]
        try:
            rep = self._ix.index_chunks(chunks, batch_size=BATCH)
        except Exception as e:
            self._reg.finish(job_id, status=JobStatus.FAILED,
                              error=f"{type(e).__name__}: {e}")
            return {"job_id": job_id, "committed": 0, "status": "failed",
                    "error": str(e)}
        self._drafts.delete(job_id)
        self._reg.finish(job_id, status=JobStatus.DONE,
                          origin_hash=job.origin_hash,
                          chunks_indexed=rep.indexed)
        return {"job_id": job_id, "committed": rep.indexed,
                "skipped": rep.skipped, "status": "done"}

    def reject(self, job_id: str) -> dict:
        job = self._reg.get(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        self._drafts.delete(job_id)
        self._reg.finish(job_id, status=JobStatus.REJECTED,
                          error="user rejected")
        return {"job_id": job_id, "status": "rejected"}


_DEFAULT: Optional[JobCommitter] = None


def get_default_committer(indexer: Any = None) -> Optional[JobCommitter]:
    global _DEFAULT
    if _DEFAULT is None and indexer is not None:
        _DEFAULT = JobCommitter(indexer=indexer)
    return _DEFAULT


def set_default_committer(c: Optional[JobCommitter]) -> None:
    global _DEFAULT
    _DEFAULT = c


__all__ = ["JobCommitter", "get_default_committer",
           "set_default_committer"]
