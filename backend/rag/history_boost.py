"""多轮会话记忆加权（单一职责）。

职责：
  - 从 history 提取 class_name 集合
  - 对命中过的类做乘性 boost
不做：
  - 不检索、不编码、不做 RRF（orchestrator 管）
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Iterable, List, Set

logger = logging.getLogger(__name__)


def extract_classes_from_history(history) -> Set[str]:
    """从历史文本里提取出现过的药材名（用 query_rewriter 药名词表）。"""
    if not history:
        return set()
    try:
        from backend.agent_tools.query_rewriter import _load_herb_vocab
        vocab = _load_herb_vocab() or set()
    except Exception:
        vocab = set()
    if not vocab:
        return set()
    classes: Set[str] = set()
    for h in history:
        s = str(h or "")
        for name in vocab:
            if name and name in s:
                classes.add(name)
    return classes


def boost_by_history(hits: List[Dict[str, Any]],
                     history_classes: Set[str],
                     boost: float = 1.5) -> List[Dict[str, Any]]:
    """对 history_classes 里的 class_name 命中提权（乘性），返回新列表。"""
    if not history_classes or not hits:
        return hits
    for h in hits:
        cls = h.get("class_name", "")
        if cls and cls in history_classes:
            h["score"] = float(h.get("score") or 0.0) * boost
            h["_boosted"] = True
    hits.sort(key=lambda x: -float(x.get("score") or 0.0))
    return hits


__all__ = ["extract_classes_from_history", "boost_by_history"]
