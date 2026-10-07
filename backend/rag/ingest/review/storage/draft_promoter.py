"""L2 草稿提升器 —— 只负责写向量库，状态流转由 ApprovalRouter 统一管理。"""
from __future__ import annotations

from typing import Protocol, Sequence

from backend.rag.ingest.review.storage.draft_store_contract import DraftStoreContract


class VectorWriterPort(Protocol):
    def upsert(self, chunk_id: str, content: str, metadata: dict) -> None: ...


class DraftPromoter:
    """将草稿块写入向量库；upsert 天然幂等，无需 exists 前置检查。"""

    def __init__(self, store: DraftStoreContract, writer: VectorWriterPort) -> None:
        self._store = store
        self._writer = writer

    def promote(self, job_id: str, approved_ids: Sequence[str]) -> int:
        return self._write_approved(job_id, approved_ids)

    def _write_approved(self, job_id: str, approved_ids: Sequence[str]) -> int:
        allow = set(approved_ids)
        count = 0
        for chunk in self._store.get_chunks(job_id):
            if allow and chunk.chunk_id not in allow:
                continue
            self._writer.upsert(chunk.chunk_id, chunk.content, dict(chunk.metadata))
            count += 1
        return count
