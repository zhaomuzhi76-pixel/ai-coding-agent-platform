"""L3 Reranker 适配器 —— 匹配现有顶层 rerank(query, docs, top_k)。"""
from __future__ import annotations

import importlib
from typing import Any, Sequence

_MODULE = "backend.rag.reranker_server"
_FN = "rerank"
_WRAPPER_KEYS = (
    "results", "data", "items", "scores",
    "hits", "documents", "docs", "list", "output",
)


class RerankerAdapter:
    """把现有 rerank 适配为 rerank(query, texts) -> list[float]。

    raw 形态覆盖：
      A. [score, ...]                 与 texts 同序
      B. [(doc, score), ...]          按 doc 文本匹配
      C. [{"doc":..., "score":...}, ...]
      D. [doc, ...]                   重排后文档列表（rank 分）
      E. {"results": [...], ...}      包装字典，自动解包
    """

    def __init__(self, fn: Any | None = None) -> None:
        self._fn = fn if fn is not None else _load_fn()

    @property
    def backend(self) -> str:
        return "real" if self._fn is not None else "fallback"

    def rerank(self, query: str, texts: Sequence[str]) -> list[float]:
        n = len(texts)
        if self._fn is None or n == 0:
            return [0.0] * n
        raw = self.call_raw(query, texts)
        return _map_scores(raw, texts, n)

    def call_raw(self, query: str, texts: Sequence[str]) -> Any:
        if self._fn is None:
            return None
        n = len(texts)
        for args, kwargs in (
            ((query, list(texts), n), {}),
            ((query, list(texts)), {"top_k": n}),
            ((query, list(texts)), {}),
        ):
            try:
                return self._fn(*args, **kwargs)
            except TypeError:
                continue
            except Exception as e:
                return {"__error__": f"{type(e).__name__}: {e}"}
        return None


def _map_scores(raw: Any, texts: Sequence[str], n: int) -> list[float]:
    items = _unwrap(raw)
    if items is None or not items:
        return [0.0] * n

    if _is_pure_floats(items, n):
        return [float(v) for v in items]

    scores = [0.0] * n
    pos = {t: i for i, t in enumerate(texts)}
    for rank, item in enumerate(items):
        doc, val = _unpack(item)
        if doc is None:
            continue
        idx = pos.get(doc)
        if idx is None:
            idx = _fallback_index(doc, texts)
        if idx is not None and 0 <= idx < n:
            scores[idx] = _to_float(val) if val is not None else _rank_score(rank, n)
    return scores


def _unwrap(raw: Any) -> list | None:
    """把包装字典解包为 list。"""
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, tuple):
        return list(raw)
    if isinstance(raw, dict):
        for key in _WRAPPER_KEYS:
            inner = raw.get(key)
            if isinstance(inner, (list, tuple)):
                return list(inner)
        # 兜底：dict 里第一个 list 值
        for v in raw.values():
            if isinstance(v, (list, tuple)):
                return list(v)
        return None
    return None


def _is_pure_floats(items: list, n: int) -> bool:
    if len(items) != n:
        return False
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in items)


def _unpack(item: Any) -> tuple[str | None, Any]:
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return str(item[0]), item[1]
    if isinstance(item, dict):
        doc = _doc_of(item)
        val = _val_of(item)
        return doc, val
    if isinstance(item, str):
        return item, None
    return None, None


def _doc_of(d: dict) -> str | None:
    for key in ("doc", "text", "content", "document", "chunk", "body"):
        v = d.get(key)
        if isinstance(v, str) and v:
            return v
    return None


def _val_of(d: dict) -> Any:
    for key in ("score", "relevance", "logit", "prob", "similarity", "value"):
        if key in d:
            return d[key]
    return None


def _fallback_index(doc: str, texts: Sequence[str]) -> int | None:
    key = doc[: min(80, len(doc))]
    for i, t in enumerate(texts):
        if t == doc or t.startswith(key) or doc.startswith(t[: min(80, len(t))]):
            return i
    return None


def _rank_score(rank: int, n: int) -> float:
    return 1.0 - (rank / max(n, 1))


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _load_fn() -> Any | None:
    try:
        module = importlib.import_module(_MODULE)
    except Exception:
        return None
    fn = getattr(module, _FN, None)
    return fn if callable(fn) else None


def build_reranker(fn: Any | None = None) -> RerankerAdapter:
    return RerankerAdapter(fn)
