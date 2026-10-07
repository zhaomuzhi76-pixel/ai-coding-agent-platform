"""models 列表 + selection 切换 handler（框架无关）+ 可选 FastAPI 挂载。
职责：只处理"选择"相关协议，不处理 chat。"""
from __future__ import annotations
from typing import Any, Callable
from backend.api.chatbot.binding import (parse_selection_body, render_model_list)
from backend.application.chatbot.service import ChatbotService

def list_models_handler(model_catalog, embedding_catalog, rerank_catalog) -> dict:
    return render_model_list(model_catalog, embedding_catalog, rerank_catalog)

def get_binding_handler(service: ChatbotService, session_id: str) -> dict:
    if not session_id:
        raise ValueError("session_id must not be empty")
    b = service.get_binding(session_id)
    return {"llm_id": b.llm_id, "image_gen_id": b.image_gen_id,
            "embedding_id": b.embedding_id, "rerank_id": b.rerank_id}

def set_selection_handler(service: ChatbotService, session_id: str, raw_body: Any) -> dict:
    if not session_id:
        raise ValueError("session_id must not be empty")
    body = parse_selection_body(raw_body)
    if body.llm_id is not None:
        service.set_llm(session_id, body.llm_id)
    if body.image_gen_id is not None or "image_gen_id" in (raw_body or {}):
        service.set_image_gen(session_id, body.image_gen_id)
    b = service.get_binding(session_id)
    return {"llm_id": b.llm_id, "image_gen_id": b.image_gen_id}

def register_selection_routes(router: Any,
                               get_service: Callable[[], ChatbotService],
                               get_catalogs: Callable[[], tuple]) -> None:
    """FastAPI 挂载。未安装 fastapi 时抛错，但不影响本模块导入。"""
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装，无法挂载 selection routes") from e

    @router.get("/api/chatbot/models")
    def _list_models() -> dict:
        mc, ec, rc = get_catalogs()
        return list_models_handler(mc, ec, rc)

    @router.get("/api/chatbot/{session_id}/selection")
    def _get_selection(session_id: str) -> dict:
        return get_binding_handler(get_service(), session_id)

    @router.post("/api/chatbot/{session_id}/selection")
    def _set_selection(session_id: str, body: dict) -> dict:
        return set_selection_handler(get_service(), session_id, body)
