"""答案相关性：query 与 answer 的 token 重叠率。"""
from __future__ import annotations

import re
from typing import Set

from backend.config.rag_governance import get_rag_config

from .contracts import RelevanceReport

_WORD = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")
# 停用词表 → backend/data/rag_stopwords_zh.json
# 兼容旧名字 `_STOP`：模块 __getattr__ 动态代理


def _stopwords() -> frozenset:
    """动态读停用词表（支持 env 更新 + cache_clear 后 reload）。"""
    return get_rag_config().stopwords


def __getattr__(name: str):
    if name == "_STOP":
        return _stopwords()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _tokens(text: str) -> Set[str]:
    return {
        m.group(0).lower()
        for m in _WORD.finditer(text or "")
        if m.group(0).lower() not in _stopwords()
    }


def score_relevance(query: str, answer: str) -> RelevanceReport:
    """query 关键 token 在 answer 中的覆盖率。"""
    q = _tokens(query)
    a = _tokens(answer)
    if not q:
        return RelevanceReport(score=1.0)
    overlap = sorted(q & a)
    missing = sorted(q - a)
    return RelevanceReport(
        score=len(overlap) / len(q),
        overlap_terms=overlap,
        missing_terms=missing,
    )


__all__ = ["score_relevance"]
