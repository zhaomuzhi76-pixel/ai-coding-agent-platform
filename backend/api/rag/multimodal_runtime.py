"""Multimodal RAG runtime 单例。职责：构造 VectorStore + embed + service，
暴露 router builder。不挂路由逻辑、不解析协议、不写盘。
与 api/rag/router.py 边界：现有 router 管纯文本 RAG；本文件管图文混合。"""
from __future__ import annotations
from backend.config.constants.endpoints import (
    OLLAMA_URL,
)

from backend.core.observability.silent import swallow

from dataclasses import dataclass
from typing import Any, Optional

from backend.api.rag.multimodal_router import register_multimodal_routes
from backend.providers.runtime.ollama_embed import make_embed_fn
from backend.rag.multimodal.service import make_service
from backend.storage.vector_backend import get_vector_store
from backend.storage.vector_config import VectorConfig

def _pick_embed_model(preferred: str) -> str:
    """优先用 preferred；Ollama 找不到时从 tags 里挑第一个含 embed 的。"""
    import json as _json
    import sys as _sys
    import urllib.request as _url
    from backend.providers.runtime.ollama_embed import OllamaEmbedClient

    # 1) 试 preferred
    try:
        OllamaEmbedClient(model=preferred, timeout=10).embed(["ping"])
        return preferred
    except Exception as e:
        print(f"[multimodal_runtime] 首选 {preferred} 不可用: {e}",
              file=_sys.stderr)

    # 2) 从 tags 找
    try:
        ep = OLLAMA_URL
        with _url.urlopen(f"{ep}/api/tags", timeout=5) as r:
            data = _json.loads(r.read().decode("utf-8"))
        for m in data.get("models", []):
            name = str(m.get("name", ""))
            if "embed" in name.lower():
                print(f"[multimodal_runtime] 自动选中 {name}",
                      file=_sys.stderr)
                return name
    except Exception as e:
        swallow("api.rag.multimodal_runtime:43", e, level="warn")
    return preferred


def _build_vector_store() -> Any:
    """通过工厂选后端（默认 Chroma，env VECTOR_BACKEND=qdrant 时用 Qdrant）。"""
    return get_vector_store(VectorConfig())

@dataclass(frozen=True)
class MultimodalRagRuntime:
    service: Any
    embed_client: Any
    vector_store: Any

def build_multimodal_rag_runtime() -> MultimodalRagRuntime:
    vs = _build_vector_store()
    configured = getattr(getattr(vs, "config", None), "embedding_model", "") \
        or VectorConfig().embedding_model
    model = _pick_embed_model(configured)
    embed = make_embed_fn(model=model)
    svc = make_service(vector_store=vs, embed_fn=embed)
    return MultimodalRagRuntime(service=svc, embed_client=embed, vector_store=vs)

_RUNTIME: Optional[MultimodalRagRuntime] = None

def get_multimodal_rag_runtime() -> MultimodalRagRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = build_multimodal_rag_runtime()
    return _RUNTIME

def set_multimodal_rag_runtime(rt: Optional[MultimodalRagRuntime]) -> None:
    global _RUNTIME
    _RUNTIME = rt

def build_multimodal_rag_router() -> Any:
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装，无法构建 multimodal rag router") from e
    router = APIRouter()
    register_multimodal_routes(router, lambda: get_multimodal_rag_runtime().service)
    return router
