"""Chatbot runtime 单例。职责：装配 service + 三目录 + 真桥（Ollama / DashScope）。
不挂路由、不做协议解析、不写盘。"""
from __future__ import annotations
from backend.core.model_registry.legacy_compat import _default_role_model, _default_provider_id
from dataclasses import dataclass
from typing import Optional
from backend.application.chatbot.service import ChatbotService
from backend.application.chatbot.service_factory import build_chatbot_service
from backend.providers.runtime.ollama_client import OllamaClient
from backend.providers.selection.model_catalog import ModelCatalog
from backend.providers.selection.session_binding import SessionBindingStore
from backend.rag.selection.embedding_catalog import EmbeddingCatalog
from backend.rag.selection.rerank_catalog import RerankCatalog
from backend.runtime.plugins.chatbot.image_gen_bridge import ImageGenBridge
from backend.runtime.plugins.chatbot.llm_bridge import LlmBridge

FALLBACK_LLMS = (
    {"id": "qwen2.5:0.5b", "provider": _default_provider_id(),
     "input_modalities": ["text"], "output_modalities": ["text"]},
)

DEFAULT_IMAGE_GENS = (
    {"id": "wanx2.1-t2i-turbo", "provider": "dashscope",
     "display": "wanx2.1-t2i-turbo · dashscope"},
)

DEFAULT_EMBEDDINGS = (
    {"id": "bge-m3", "provider": "local", "dim": 1024},
    {"id": "bge-large-zh", "provider": "local", "dim": 1024},
)

DEFAULT_RERANKS = (
    {"id": "bge-reranker-v2", "provider": "local"},
)

@dataclass(frozen=True)
class ChatbotRuntime:
    service: ChatbotService
    model_catalog: ModelCatalog
    embedding_catalog: EmbeddingCatalog
    rerank_catalog: RerankCatalog
    rag_bridge: Any = None

def _discover_llms(client: OllamaClient) -> list[dict]:
    try:
        names = client.list_models()
    except Exception:
        names = []
    out: list[dict] = []
    for n in names:
        low = n.lower()
        if "reranker" in low or "embed" in low:
            continue
        out.append({"id": n, "provider": _default_provider_id(),
                    "input_modalities": ["text"],
                    "output_modalities": ["text"]})
    return out or [dict(FALLBACK_LLMS[0])]

def _register_defaults(mc: ModelCatalog, ec: EmbeddingCatalog,
                       rc: RerankCatalog, llms: list[dict]) -> None:
    for spec in llms:
        mc.register({**spec, "kind": "llm"})
    for spec in DEFAULT_IMAGE_GENS:
        mc.register({**spec, "kind": "image_gen",
                     "input_modalities": ["text"],
                     "output_modalities": ["image"]})
    for spec in DEFAULT_EMBEDDINGS:
        ec.register(spec["id"], spec["provider"], spec["dim"])
    for spec in DEFAULT_RERANKS:
        rc.register(spec["id"], spec["provider"])

def _build_rag_bridge() -> Any:
    """尝试装配 RAG 桥。失败时降级为 None（chatbot 仍可用）。"""
    try:
        from backend.api.rag.multimodal_runtime import get_multimodal_rag_runtime
        from backend.runtime.plugins.chatbot.rag_bridge import make_rag_bridge
        rt = get_multimodal_rag_runtime()
        return make_rag_bridge(rt.service, top_k=3)
    except Exception:
        return None

def build_chatbot_runtime() -> ChatbotRuntime:
    client = OllamaClient()
    llms = _discover_llms(client)
    mc = ModelCatalog(); ec = EmbeddingCatalog(); rc = RerankCatalog()
    _register_defaults(mc, ec, rc, llms)
    store = SessionBindingStore()
    rag = _build_rag_bridge()
    service = build_chatbot_service(
        session_store=store, model_catalog=mc,
        llm_bridge=LlmBridge(client),
        image_gen_bridge=ImageGenBridge(),
        rag_bridge=rag,
    )
    return ChatbotRuntime(service=service, model_catalog=mc,
                          embedding_catalog=ec, rerank_catalog=rc,
                          rag_bridge=rag)

_RUNTIME: Optional[ChatbotRuntime] = None

def get_runtime() -> ChatbotRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = build_chatbot_runtime()
    return _RUNTIME

def set_runtime(runtime: Optional[ChatbotRuntime]) -> None:
    global _RUNTIME
    _RUNTIME = runtime
