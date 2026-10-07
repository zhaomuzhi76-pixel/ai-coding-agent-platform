"""Reranker HTTP 客户端。职责：POST /rerank 拿精排分数。
不做融合（fusion 管）、不做检索（retriever 管）。
降级策略：连不上/超时 → 返回空（调用方保持原顺序）。
"""
from __future__ import annotations
from backend.config.constants.endpoints import (
    RERANKER_URL,
)

import json
import os
import urllib.request
from typing import Optional, Sequence

DEFAULT_URL = os.environ.get("RERANKER_URL", RERANKER_URL)
DEFAULT_TIMEOUT = 30.0


class RerankerClient:
    def __init__(self, url: str = DEFAULT_URL,
                 timeout: float = DEFAULT_TIMEOUT) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout

    @property
    def url(self) -> str:
        return self._url

    def health(self) -> dict:
        try:
            req = urllib.request.Request(f"{self._url}/health")
            with urllib.request.urlopen(req, timeout=3) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def rerank(self, query: str, docs: Sequence[str],
               top_k: int = 5) -> list:
        """返回 [{"index": i, "score": s, "document": d}, ...] 按 score 降序。
        失败返回 []（调用方保持原顺序）。"""
        if not query or not docs:
            return []
        payload = json.dumps({
            "query": str(query),
            "documents": [str(d) for d in docs],
            "top_k": int(top_k),
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self._url}/rerank", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            results = data.get("results") or []
            return [r for r in results if isinstance(r, dict)]
        except Exception:
            return []


_DEFAULT: Optional[RerankerClient] = None


def get_default_reranker() -> RerankerClient:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = RerankerClient()
    return _DEFAULT


def set_default_reranker(c: Optional[RerankerClient]) -> None:
    global _DEFAULT
    _DEFAULT = c


__all__ = ["RerankerClient", "get_default_reranker",
           "set_default_reranker", "DEFAULT_URL"]
