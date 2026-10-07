"""检索质量指标：coverage / avg_score / top_score / MRR。"""
from __future__ import annotations

from typing import Any, Iterable, List

from .contracts import RetrievalQuality


def _score_of(h: Any) -> float:
    if isinstance(h, dict):
        v = h.get("score", 0.0)
    else:
        v = getattr(h, "score", 0.0)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def score_retrieval(
    hits: Iterable[Any],
    *,
    min_relevant: float = 0.5,
) -> RetrievalQuality:
    """coverage = 分数 ≥ min_relevant 的命中占比。"""
    arr: List[float] = [_score_of(h) for h in hits]
    if not arr:
        return RetrievalQuality(k=0)
    k = len(arr)
    above = sum(1 for s in arr if s >= min_relevant)
    coverage = above / k
    top = max(arr)
    avg = sum(arr) / k
    # MRR：第一条 ≥ min_relevant 的排名倒数
    mrr = None
    for i, s in enumerate(arr, 1):
        if s >= min_relevant:
            mrr = 1.0 / i
            break
    return RetrievalQuality(
        k=k, coverage=coverage,
        avg_score=avg, top_score=top,
        mrr=mrr,
    )


__all__ = ["score_retrieval"]
