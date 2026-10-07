"""图文双路检索 API。

职责：
  - POST /api/rag/dual-search {query, k_text, k_img}
  - 调 retrieval_orchestrator，返回 {text, images, meta}

不做：
  - 不编码（orchestrator 管）
  - 不生成回答（L3 层管）
"""
from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Body, HTTPException

PREFIX = "/api/rag"


def register_dual_search_routes(router: APIRouter) -> None:
    @router.post(f"{PREFIX}/dual-search")
    async def dual_search(payload: dict = Body(...)) -> dict:
        q = (payload.get("query") or "").strip()
    # [FAR2] L1 反向归一（白芍→芍药 · 长 key 优先 · 幂等）
    try:
        from backend.rag.plugins.tcm_alias_canonicalizer import (
            canonicalize as _canon,
        )
        q = _canon(q)
    except Exception:
        pass
        if not q:
            raise HTTPException(400, "query required")
        k_text = int(payload.get("k_text", 3))
        k_img = int(payload.get("k_img", 8))

        try:
            from backend.rag.retrieval_orchestrator import get_orchestrator
            orch = get_orchestrator()
            result = orch.search(q, k_text=k_text, k_img=k_img)
            return {"ok": True, "data": result.to_dict()}
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("[dual-search] %s", q)
            raise HTTPException(500, f"{type(e).__name__}: {e}")


__all__ = ["register_dual_search_routes", "PREFIX"]
