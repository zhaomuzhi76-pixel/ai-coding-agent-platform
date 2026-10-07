"""Provider composition root.

从 backend/config/llm_providers.yaml 读多 provider 配置。
无配置时抛错——不再回退硬编码。
"""
from __future__ import annotations
from backend.config.constants.endpoints import (
    OLLAMA_URL,
)

from typing import Any, Dict

from backend.providers.assembly.capability_assembly import (
    CapabilityAssembly,
)
from backend.providers.assembly.configuration import (
    ProviderAssemblyConfiguration,
)
from backend.providers.assembly.context import (
    ProviderAssemblyContext,
)
from backend.providers.assembly.provider_assembly import (
    ProviderAssembly,
)
from backend.providers.assembly.runtime_assembly import (
    RuntimeAssembly,
)
from backend.providers.capability.registry import (
    ProviderCapabilityRegistry,
)
from backend.providers.implementations.ollama_provider import (
    OllamaProvider,
)
from backend.providers.implementations.openai_provider import (
    OpenAICompatibleProvider,
)
from backend.providers.implementations.dashscope_provider import (
    DashScopeProvider,
)
from backend.providers.implementations.anthropic_provider import (
    AnthropicProvider,
)
from backend.providers.registry import (
    ProviderRegistry,
)


_TYPE_CLASS = {
    "ollama": OllamaProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "dashscope": DashScopeProvider,
    "anthropic": AnthropicProvider,
}


class ProviderAssemblyBuilder:
    """Provider composition root driven by llm_providers.yaml."""

    VERSION = "7.0"

    def __init__(
        self,
        configuration: ProviderAssemblyConfiguration | None = None,
    ) -> None:
        self.configuration = (
            configuration
            if configuration is not None
            else ProviderAssemblyConfiguration()
        )

        if not isinstance(
            self.configuration,
            ProviderAssemblyConfiguration,
        ):
            raise TypeError(
                "provider assembly configuration required"
            )

        self.provider_registry = ProviderRegistry()
        self.capability_registry = (
            ProviderCapabilityRegistry()
        )
        self.provider_assembly = ProviderAssembly(
            self.provider_registry
        )
        self.capability_assembly = CapabilityAssembly(
            self.capability_registry
        )
        self.runtime_assembly = RuntimeAssembly()

    def build(self) -> ProviderAssemblyContext:
        provider_types = self._provider_types()
        adapters, providers = (
            self.provider_assembly.build(provider_types)
        )

        if not adapters or not providers:
            raise RuntimeError(
                "provider assembly produced no providers"
            )

        # 用「注册名」绑定，避免实例 .name 与注册名不一致
        provider_names = tuple(
            str(cfg.get("name", key))
            for key, cfg in provider_types.items()
        )
        self.capability_assembly.bind(
            providers, provider_names=provider_names,
        )

        context = ProviderAssemblyContext(
            provider_registry=self.provider_registry,
            provider_bridge=self.provider_assembly.bridge,
            capability_registry=self.capability_registry,
            capability_bridge=self.capability_assembly.bridge,
            capability_resolver=self.capability_assembly.resolver,
        )

        default_provider = self._resolve_default_provider()
        self.runtime_assembly.build(context, default_provider)

        if not context.ready():
            raise RuntimeError(
                "provider assembly unavailable"
            )

        return context

    def _provider_types(self) -> Dict[str, Dict[str, Any]]:
        cfg = self._load_config()
        out: Dict[str, Dict[str, Any]] = {}
        for p in cfg.providers:
            cls = _TYPE_CLASS.get(p.type)
            if cls is None:
                continue
            first_model = p.models[0].id if p.models else ""
            if not first_model:
                continue
            kwargs = self._provider_kwargs(
                p.type, first_model, p.base_url, p.api_key,
            )
            if kwargs is None:
                continue
            key = f"{p.type}::{p.name}"
            out[key] = {
                "name": p.name,
                "category": "llm",
                "provider_class": cls,
                "config": kwargs,
            }
        if not out:
            raise RuntimeError(
                "no llm provider configured; "
                "check backend/config/llm_providers.yaml"
            )
        return out

    def _load_config(self):
        from backend.providers.config import load_llm_config
        cfg = load_llm_config()
        if not cfg.providers:
            raise RuntimeError(
                "llm_providers.yaml loaded no providers "
                f"(skipped={cfg.skipped})"
            )
        return cfg

    def _resolve_default_provider(self) -> str:
        cfg = self._load_config()
        if cfg.default_provider:
            return cfg.default_provider
        return cfg.providers[0].name

    @staticmethod
    def _provider_kwargs(
        ptype: str,
        first_model: str,
        base_url: str,
        api_key: str,
    ) -> Dict[str, Any] | None:
        if ptype == "ollama":
            return {
                "model": first_model,
                "base_url": base_url or OLLAMA_URL,
            }
        if ptype == "openai_compatible":
            return {
                "model": first_model,
                "base_url": base_url,
                "api_key": api_key or "EMPTY",
            }
        if ptype == "dashscope":
            return {
                "api_key": api_key,
                "base_url": base_url,
                "default_model": first_model,
            }
        if ptype == "anthropic":
            return {
                "api_key": api_key,
                "base_url": base_url,
                "default_model": first_model,
            }
        return None

    def ready(self) -> bool:
        return (
            self.provider_assembly.ready()
            and self.capability_assembly.ready()
        )

    def dump(self) -> Dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "provider": self.provider_assembly.dump(),
            "capability": self.capability_assembly.dump(),
            "runtime": self.runtime_assembly.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ProviderAssemblyBuilder",
]
