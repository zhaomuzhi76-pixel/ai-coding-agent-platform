"""Chatbot 服务装配。职责：构造 Service 及其依赖，不做业务。"""
from __future__ import annotations
from typing import Any
from backend.application.chatbot.service import ChatbotService
from backend.providers.selection.model_catalog import ModelCatalog
from backend.providers.selection.session_binding import SessionBindingStore
from backend.runtime.plugins.chatbot import ChatbotPlugin

def build_chatbot_service(*, session_store: SessionBindingStore,
                          model_catalog: ModelCatalog,
                          llm_bridge: Any = None,
                          image_gen_bridge: Any = None,
                          rag_bridge: Any = None) -> ChatbotService:
    plugin = ChatbotPlugin(session_store=session_store, model_catalog=model_catalog)
    return ChatbotService(plugin=plugin, session_store=session_store,
                          model_catalog=model_catalog,
                          llm_bridge=llm_bridge,
                          image_gen_bridge=image_gen_bridge,
                          rag_bridge=rag_bridge)
