"""Chatbot FastAPI APIRouter 装配。职责：创建 router，挂 chat + selection 路由。
不实现 handler、不持有 runtime。"""
from __future__ import annotations
from typing import Any, Callable
from backend.api.chatbot.runtime import get_runtime
from backend.api.chatbot.router import register_chat_routes
from backend.api.chatbot.selection_router import register_selection_routes

def build_chatbot_router() -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as e:
        raise RuntimeError("fastapi 未安装，无法构建 chatbot router") from e

    router = APIRouter()

    def _service():
        return get_runtime().service

    def _catalogs() -> tuple:
        rt = get_runtime()
        return (rt.model_catalog, rt.embedding_catalog, rt.rerank_catalog)

    register_chat_routes(router, _service)
    register_selection_routes(router, _service, _catalogs)
    return router
