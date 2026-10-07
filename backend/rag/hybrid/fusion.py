"""多路命中融合。职责：向量命中 + BM25 命中 → 融合后的 HybridHit 列表。
支持策略：RRF（推荐）、WEIGHTED、VECTOR_ONLY、BM25_ONLY。
不做检索（retriever 管）、不索引（bm25_index 管）、不做序列化（contracts 管）。
输入规范：
  向量 hits：list[dict] 必含 chunk_id/text/score，可含 source/metadata
  BM25 hits：list[tuple] (chunk_id, score, text, meta)
"""
from __future__ import annotations
from typing import Any, Mapping, Sequence, Tuple

from backend.rag.hybrid.contracts import (
    FusionStrategy, HybridHit)

DEFAULT_RRF_K = 60
DEFAULT_VECTOR_WEIGHT = 0.7
DEFAULT_BM25_WEIGHT = 0.3


# ---------- 输入规整 ----------
def _normalize_vector_hits(hits: Sequence[Any]) -> list:
    out: list = []
    for h in hits or ():
        if isinstance(h, Mapping):
            cid = str(h.get("chunk_id", ""))
            text = str(h.get("text", ""))
            score = float(h.get("score", 0.0) or 0.0)
            src = str(h.get("source", ""))
            meta = dict(h.get("metadata") or {})
        else:
            cid = str(getattr(h, "chunk_id", ""))
            text = str(getattr(h, "text", ""))
            score = float(getattr(h, "score", 0.0) or 0.0)
            src = str(getattr(h, "source", ""))
            meta = dict(getattr(h, "metadata", {}) or {})
        if cid:
            out.append({"chunk_id": cid, "text": text,
                        "score": score, "source": src, "meta": meta})
    return out


def _normalize_bm25_hits(hits: Sequence[Any]) -> list:
    out: list = []
    for h in hits or ():
        if isinstance(h, (list, tuple)) and len(h) >= 4:
            cid, score, text, meta = h[0], h[1], h[2], h[3]
            out.append({"chunk_id": str(cid), "text": str(text),
                        "score": float(score or 0.0),
                        "source": "", "meta": dict(meta or {})})
        elif isinstance(h, Mapping):
            cid = str(h.get("chunk_id", ""))
            if cid:
                out.append({"chunk_id": cid, "text": str(h.get("text", "")),
                            "score": float(h.get("score", 0.0) or 0.0),
                            "source": "", "meta": dict(h.get("metadata") or {})})
    return out


# ---------- 融合策略 ----------
def _rrf_merge(vec: list, bm25: list, k: int) -> dict:
    """返回 chunk_id -> {vec_rank, bm25_rank, fused_score}。"""
    acc: dict = {}
    for rank, h in enumerate(vec, 1):
        e = acc.setdefault(h["chunk_id"], {"vec": None, "bm25": None,
                                             "vscore": 0.0, "bscore": 0.0,
                                             "text": h["text"], "src": h["source"],
                                             "meta": h["meta"]})
        e["vec"] = rank; e["vscore"] = h["score"]
    for rank, h in enumerate(bm25, 1):
        e = acc.setdefault(h["chunk_id"], {"vec": None, "bm25": None,
                                             "vscore": 0.0, "bscore": 0.0,
                                             "text": h["text"], "src": h["source"],
                                             "meta": h["meta"]})
        e["bm25"] = rank; e["bscore"] = h["score"]
    for cid, e in acc.items():
        s = 0.0
        if e["vec"] is not None:
            s += 1.0 / (k + e["vec"])
        if e["bm25"] is not None:
            s += 1.0 / (k + e["bm25"])
        e["score"] = s
    return acc


def _minmax(vals: list) -> Tuple[float, float]:
    if not vals:
        return 0.0, 1.0
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return 0.0, 1.0
    return lo, hi


def _weighted_merge(vec: list, bm25: list,
                    vw: float, bw: float) -> dict:
    """分数归一化后加权。"""
    v_scores = [h["score"] for h in vec]
    b_scores = [h["score"] for h in bm25]
    vlo, vhi = _minmax(v_scores)
    blo, bhi = _minmax(b_scores)
    acc: dict = {}
    for rank, h in enumerate(vec, 1):
        n = (h["score"] - vlo) / (vhi - vlo)
        acc.setdefault(h["chunk_id"], {"vec": None, "bm25": None,
                                        "vscore": 0.0, "bscore": 0.0,
                                        "text": h["text"], "src": h["source"],
                                        "meta": h["meta"]})
        acc[h["chunk_id"]]["vec"] = rank
        acc[h["chunk_id"]]["vscore"] = h["score"]
        acc[h["chunk_id"]]["score"] = vw * n
    for rank, h in enumerate(bm25, 1):
        n = (h["score"] - blo) / (bhi - blo)
        e = acc.setdefault(h["chunk_id"], {"vec": None, "bm25": None,
                                             "vscore": 0.0, "bscore": 0.0,
                                             "text": h["text"], "src": h["source"],
                                             "meta": h["meta"]})
        e["bm25"] = rank
        e["bscore"] = h["score"]
        e["score"] = e.get("score", 0.0) + bw * n
    return acc


# ---------- 对外接口 ----------
def fuse(
    *,
    query: str,
    vector_hits: Sequence[Any] = (),
    bm25_hits: Sequence[Any] = (),
    strategy: FusionStrategy = FusionStrategy.RRF,
    top_k: int = 10,
    rrf_k: int = DEFAULT_RRF_K,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    bm25_weight: float = DEFAULT_BM25_WEIGHT,
) -> list:
    """融合返回 list[HybridHit] 按 fused_score 降序。"""
    if top_k <= 0:
        raise ValueError("top_k must be > 0")
    if rrf_k <= 0:
        raise ValueError("rrf_k must be > 0")
    if strategy == FusionStrategy.VECTOR_ONLY:
        merged = _rrf_merge(_normalize_vector_hits(vector_hits), [], rrf_k)
    elif strategy == FusionStrategy.BM25_ONLY:
        merged = _rrf_merge([], _normalize_bm25_hits(bm25_hits), rrf_k)
    else:
        vec = _normalize_vector_hits(vector_hits)
        bm = _normalize_bm25_hits(bm25_hits)
        if strategy == FusionStrategy.RRF:
            merged = _rrf_merge(vec, bm, rrf_k)
        elif strategy == FusionStrategy.WEIGHTED:
            merged = _weighted_merge(vec, bm, vector_weight, bm25_weight)
        else:
            raise ValueError(f"未知策略: {strategy}")

    out: list = []
    for cid, e in merged.items():
        out.append(HybridHit(
            chunk_id=cid, text=e.get("text", ""),
            fused_score=float(e.get("score", 0.0)),
            vector_rank=e.get("vec"), bm25_rank=e.get("bm25"),
            vector_score=float(e.get("vscore", 0.0)),
            bm25_score=float(e.get("bscore", 0.0)),
            source=e.get("src", ""), metadata=e.get("meta", {})))
    out.sort(key=lambda h: -h.fused_score)
    return out[:top_k]


def make_fused_report(*, query: str, vector_hits, bm25_hits,
                      strategy=FusionStrategy.RRF, top_k=10,
                      elapsed_ms: int = 0):
    """便捷：返回 HybridReport。"""
    from backend.rag.hybrid.contracts import HybridReport
    hits = fuse(query=query, vector_hits=vector_hits,
                bm25_hits=bm25_hits, strategy=strategy, top_k=top_k)
    return HybridReport(
        query=query, hits=tuple(hits),
        vector_candidates=len(vector_hits or ()),
        bm25_candidates=len(bm25_hits or ()),
        fused_candidates=len(hits),
        strategy=strategy, elapsed_ms=elapsed_ms)


__all__ = ["fuse", "make_fused_report",
           "DEFAULT_RRF_K", "DEFAULT_VECTOR_WEIGHT", "DEFAULT_BM25_WEIGHT"]
