"""L4 装配。职责：聚合 handler 为可调用对象；不实现业务、不做协议解析。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from backend.api.chatbot.router import chat_handler
from backend.api.chatbot.selection_router import (
    get_binding_handler, list_models_handler, set_selection_handler)
from backend.application.chatbot.service import ChatbotService

@dataclass(frozen=True)
class ChatbotRoutes:
    chat: Callable[[str, Any], dict]
    list_models: Callable[[], dict]
    get_binding: Callable[[str], dict]
    set_selection: Callable[[str, Any], dict]

def build_chatbot_routes(*, service: ChatbotService,
                         model_catalog, embedding_catalog, rerank_catalog) -> ChatbotRoutes:
    return ChatbotRoutes(
        chat=lambda sid, body: chat_handler(service, sid, body),
        list_models=lambda: list_models_handler(model_catalog,
                                                 embedding_catalog, rerank_catalog),
        get_binding=lambda sid: get_binding_handler(service, sid),
        set_selection=lambda sid, body: set_selection_handler(service, sid, body),
    )
