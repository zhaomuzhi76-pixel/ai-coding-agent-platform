"""召回测试路由 —— /api/rag/recall-test/*。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.api.recall_test_api import (
    RecallTestApi, build_default,
)
from backend.rag.ingest.review.storage.recall_config import (
    get_default_config,
)

PREFIX = "/api/rag/recall-test"


def build_router(api: RecallTestApi | None = None) -> Any:
    try:
        from fastapi import APIRouter, Body  # type: ignore
    except Exception:
        return None
    _api = api or build_default()
    _cfg = get_default_config()
    router = APIRouter()

    @router.get(f"{PREFIX}/models")
    def models() -> dict:
        from backend.rag.ingest.review.review.reranker_loader import (
            get_default_loader,
        )
        loader = get_default_loader()
        opts = [{"model_id": m["model_id"], "label": m["label"],
                 "backend_kind": "gguf", "selectable": True}
                for m in loader.list_models()]
        opts.append({"model_id": "none",
                     "label": "不精排（仅 RRF 融合）",
                     "backend_kind": "none", "selectable": True})
        default = loader.list_models()[0]["model_id"] if opts and len(opts) > 1 \
            else "none"
        return {"models": opts, "default": default}

    @router.post(f"{PREFIX}/query")
    async def query(payload: dict = Body(...)) -> dict:
        return await _api.query(
            query=str(payload.get("query") or ""),
            top_k=int(payload.get("top_k") or 10),
            use_reranker=bool(payload.get("use_reranker", True)),
            reranker_model_id=str(payload.get("reranker_model_id")
                                  or "builtin-qwen3-reranker"),
            rrf_k=int(payload.get("rrf_k") or 60),
            vector_weight=float(payload.get("vector_weight") or 0.7),
            bm25_weight=float(payload.get("bm25_weight") or 0.3),
            strategy=str(payload.get("strategy") or "rrf"),
        )

    @router.get(f"{PREFIX}/config")
    def get_config() -> dict:
        return {"config": _cfg.get().to_dict(), "version": _cfg.version()}

    @router.post(f"{PREFIX}/apply")
    def apply_config(payload: dict = Body(...)) -> dict:
        cfg = _cfg.apply(
            top_k=int(payload.get("top_k") or 10),
            use_reranker=bool(payload.get("use_reranker", True)),
            reranker_model_id=str(payload.get("reranker_model_id")
                                  or "builtin-qwen3-reranker"),
            rrf_k=int(payload.get("rrf_k") or 60),
            vector_weight=float(payload.get("vector_weight") or 0.7),
            bm25_weight=float(payload.get("bm25_weight") or 0.3),
        )
        return {"applied": True, "config": cfg.to_dict(),
                "version": _cfg.version()}

    @router.post(f"{PREFIX}/reset")
    def reset_config() -> dict:
        cfg = _cfg.reset()
        return {"reset": True, "config": cfg.to_dict(),
                "version": _cfg.version()}

    return router
