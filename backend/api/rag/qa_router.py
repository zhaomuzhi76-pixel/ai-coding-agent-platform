"""RAG QA API 端点。

POST /api/rag/qa {query, k_text?, k_img?, generate?}
→ {answer, citations, images, meta}
"""
from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Body, HTTPException

PREFIX = "/api/rag"


def register_qa_routes(router: APIRouter) -> None:
    @router.post(f"{PREFIX}/qa")
    async def rag_qa(payload: dict = Body(...)) -> dict:
        q = (payload.get("query") or "").strip()
        if not q:
            raise HTTPException(400, "query required")
        try:
            from backend.rag.rag_qa import answer
            r = answer(
                q,
                k_text=int(payload.get("k_text", 3)),
                k_img=int(payload.get("k_img", 8)),
                generate=bool(payload.get("generate", True)),
            )
            return {"ok": True, "data": r.to_dict()}
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("[rag-qa] %s", q)
            raise HTTPException(500, f"{type(e).__name__}: {e}")


__all__ = ["register_qa_routes", "PREFIX"]
