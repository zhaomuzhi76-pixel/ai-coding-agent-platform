"""provider_center 插件 —— 挂 /api/config/provider/* + 从 Model Registry 同步 LLM/Embedding"""
from __future__ import annotations

from typing import Any

from backend.core.model_registry.embedding_resolver import resolve_embedding_model
from backend.core.model_registry.legacy_compat import _default_role_model
from backend.core.model_registry.registry import get_registry
from backend.config.constants.endpoints import OLLAMA_URL

from backend.rag.ingest.review.provider_center.api import ProviderCenterApi
from backend.rag.ingest.review.provider_center.catalog import get_default_catalog
from backend.rag.ingest.review.provider_center.router import (
    ROUTE_PREFIX,
    build_router,
)
from backend.rag.ingest.review.provider_center.spec import (
    KIND_EMBEDDING,
    KIND_LLM,
    ProviderSpec,
)


def _register_llm_from_registry(catalog) -> None:
    """从 Model Registry 遍历已验证 chat 模型，注册到 provider_center catalog"""
    try:
        reg = get_registry()
    except Exception:
        return
    for mid in reg.verification.list_verified():
        m = reg.models.get(mid)
        if not m:
            continue
        if not reg._is_chat_model(m.id, m.display_name):
            continue
        provider = reg.providers.get(m.provider_id)
        endpoint = provider.base_url if provider else OLLAMA_URL
        backend_kind = "ollama" if (provider and provider.kind in
                                    ("ollama", "local", "ollama-local")) \
            else "openai_compatible"
        catalog.register(ProviderSpec(
            kind=KIND_LLM,
            model_id=m.id,
            display_name=f"{m.id} · {m.provider_id}",
            backend_kind=backend_kind,
            endpoint=endpoint,
            description=f"来自 Model Registry · {m.provider_id}",
            tags=(backend_kind, m.provider_id),
        ))


def _ensure_fallback_llm(catalog) -> None:
    """兜底：若 registry 一个都没验证，至少注册默认 code 角色模型"""
    if any(r.spec.kind == KIND_LLM for r in catalog._records.values()):
        return
    catalog.register(ProviderSpec(
        kind=KIND_LLM,
        model_id=_default_role_model("code"),
        display_name=f"本地 Ollama · {_default_role_model('code')}",
        backend_kind="ollama",
        endpoint=OLLAMA_URL,
        description="本地默认 LLM（未通过链路测试前不可选）",
        tags=("local", "ollama"),
    ))


def register_default_presets() -> None:
    """幂等注册：从 Model Registry 同步 + Embedding 兜底"""
    catalog = get_default_catalog()
    _register_llm_from_registry(catalog)
    _ensure_fallback_llm(catalog)
    catalog.register(ProviderSpec(
        kind=KIND_EMBEDDING,
        model_id=resolve_embedding_model(),
        display_name="Qwen3-Embedding（本地）",
        backend_kind="ollama",
        endpoint=OLLAMA_URL,
        description="本地默认 Embedding，向量库使用",
        tags=("local", "ollama"),
    ))


class ProviderCenterPlugin:
    descriptor = {
        "name": "provider_center",
        "version": "1.1.0",
        "description": "LLM / Embedding / Reranker 卡片同款门控（链路测试通过才可选）",
        "prefix": ROUTE_PREFIX,
        "kinds": (KIND_LLM, KIND_EMBEDDING),
    }

    @property
    def name(self) -> str:
        return self.descriptor["name"]

    def on_load(self, context: dict | None = None) -> None:
        register_default_presets()

    def on_unload(self) -> None:
        return None

    def build_router(self) -> Any:
        register_default_presets()
        return build_router(ProviderCenterApi())

    def build_api(self) -> ProviderCenterApi:
        register_default_presets()
        return ProviderCenterApi()


def build_plugin() -> ProviderCenterPlugin:
    return ProviderCenterPlugin()
