"""L3 BM25 打分适配器 —— 匹配现有 make_bm25_index + BM25Index.add/search。"""
from __future__ import annotations

import importlib
from typing import Any, Sequence

_MODULE = "backend.rag.hybrid.bm25_index"
_FACTORY = "make_bm25_index"
_ADD = ("add", "add_many")
_SEARCH = "search"


class Bm25ScorerAdapter:
    """每次打分构建临时索引，适配「给定文本列表打分」语义。"""

    def __init__(self, factory: Any | None = None) -> None:
        self._factory = factory if factory is not None else _load_factory()

    @property
    def backend(self) -> str:
        return "real" if self._factory is not None else "fallback"

    def score(self, query: str, texts: Sequence[str]) -> list[float]:
        n = len(texts)
        if self._factory is None or n == 0:
            return [0.0] * n
        try:
            index = self._factory()
        except Exception:
            return [0.0] * n
        ids = [f"__tmp{i}" for i in range(n)]
        for i, text in enumerate(texts):
            _try_add(index, ids[i], text)
        raw = _try_search(index, query, n)
        return _map_scores(raw, ids, n)


def _try_add(index: Any, doc_id: str, text: str) -> None:
    for name in _ADD:
        fn = getattr(index, name, None)
        if not callable(fn):
            continue
        for args in (([doc_id, text]), (doc_id, text), (text,), ({"id": doc_id, "text": text},)):
            try:
                fn(*args)
                return
            except TypeError:
                continue
            except Exception:
                return


def _try_search(index: Any, query: str, top_k: int) -> Any:
    fn = getattr(index, _SEARCH, None)
    if not callable(fn):
        return []
    for args, kwargs in (
        ((query,), {"top_k": top_k}),
        ((query, top_k), {}),
        ((query,), {}),
    ):
        try:
            return fn(*args, **kwargs)
        except TypeError:
            continue
        except Exception:
            return []
    return []


def _map_scores(raw: Any, ids: list[str], n: int) -> list[float]:
    scores = [0.0] * n
    pos = {cid: i for i, cid in enumerate(ids)}
    try:
        items = list(raw)
    except TypeError:
        return scores
    for item in items:
        cid, val = _unpack(item)
        if cid in pos:
            scores[pos[cid]] = _to_float(val)
    return scores


def _unpack(item: Any) -> tuple[str | None, Any]:
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return str(item[0]), item[1]
    if isinstance(item, dict):
        cid = item.get("id") or item.get("doc_id") or item.get("chunk_id")
        return (str(cid) if cid else None), item.get("score", 0.0)
    if isinstance(item, str):
        return item, 1.0
    return None, 0.0


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _load_factory() -> Any | None:
    try:
        module = importlib.import_module(_MODULE)
    except Exception:
        return None
    fn = getattr(module, _FACTORY, None)
    return fn if callable(fn) else None


def build_scorer(factory: Any | None = None) -> Bm25ScorerAdapter:
    return Bm25ScorerAdapter(factory)
