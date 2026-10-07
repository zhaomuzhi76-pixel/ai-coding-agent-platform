"""L23 端到端冒烟 —— 用真实后端跑完整两阶段流程（内存，零磁盘）。"""
from __future__ import annotations

from backend.rag.ingest.review.api.review_factory_production import (
    backends,
    build_production_api,
)
from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.foundation.review_contract import DraftChunk
from backend.rag.ingest.review.review.reranker_adapter import build_reranker
from backend.rag.ingest.review.storage.draft_store import get_default_draft_store

_JOB = "__smoke_job__"
_QUERY = "RAG 知识库 入库流程 审核"
_TEXTS = (
    "RAG 知识库入库流程包括解析、分块、审核、向量化四个阶段。",
    "今天天气不错，适合出门散步。",
    "审核门要求草稿状态从 pending_review 经 reviewing 到 approved。",
)


def run_smoke() -> dict:
    store = get_default_draft_store()
    _cleanup(store)
    chunks = [
        DraftChunk(chunk_id=f"c{i}", job_id=_JOB, content=t, order=i)
        for i, t in enumerate(_TEXTS)
    ]
    store.create_job(_JOB, chunks)
    api = build_production_api()

    job_created = _created(store)
    preview = api.preview_recall(_JOB, _QUERY)
    scores = preview.get("scores", [])
    nonzero = sum(
        1 for s in scores
        if s.get("bm25", 0) > 0 or s.get("rerank", 0) > 0
    )
    top = scores[0] if scores else None

    rerank_raw = _rerank_diag()

    approve = api.approve(_JOB, [c.chunk_id for c in chunks])

    result = {
        "job_created": job_created,
        "score_count": len(scores),
        "nonzero_scores": nonzero,
        "top_chunk": top["chunk_id"] if top else None,
        "top_score": top,
        "rerank_raw_shape": rerank_raw,
        "approve_result": approve,
        "job_cleaned": _JOB not in store.list_jobs(),
        "backends": backends(),
    }
    result["ok"] = (
        result["job_created"]
        and result["score_count"] == len(chunks)
        and result["nonzero_scores"] > 0
        and result["job_cleaned"]
    )
    return result


def _rerank_diag() -> dict:
    try:
        adapter = build_reranker()
        raw = adapter.call_raw(_QUERY, list(_TEXTS))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    return {
        "backend": adapter.backend,
        "type": type(raw).__name__,
        "len": _len(raw),
        "sample": _sample(raw),
    }


def _len(raw) -> int | None:
    try:
        return len(raw)
    except TypeError:
        return None


def _sample(raw) -> object:
    try:
        items = list(raw)
    except TypeError:
        return str(raw)[:200]
    if not items:
        return []
    first = items[0]
    if isinstance(first, (list, tuple)):
        return {"item_type": type(first).__name__, "arity": len(first),
                "head": str(first[0])[:80] if first else ""}
    if isinstance(first, dict):
        return {"item_type": "dict", "keys": sorted(first.keys())}
    if isinstance(first, (int, float)):
        return {"item_type": type(first).__name__, "value": float(first)}
    return {"item_type": type(first).__name__, "head": str(first)[:80]}


def _created(store) -> bool:
    try:
        return store.get_status(_JOB) is DraftStatus.PENDING_REVIEW
    except Exception:
        return False


def _cleanup(store) -> None:
    try:
        store.delete_job(_JOB)
    except Exception:  # silent-ok
        pass
