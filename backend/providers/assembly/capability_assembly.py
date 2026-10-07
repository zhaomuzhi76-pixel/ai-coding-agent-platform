"""CapabilityAssembly: 用「注册名」绑定 provider 能力。

修复：让 bind 接受显式 provider_names，覆盖 provider 实例的 .name。
避免「注册名 ollama-local」与「实例 .name ollama」不一致。
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

from backend.providers.capability import (
    ProviderCapabilityBridge,
    ProviderCapabilityRegistry,
    ProviderCapabilityResolver,
)


class CapabilityAssembly:
    """Assemble provider capability bindings."""

    VERSION = "1.1"

    def __init__(
        self,
        registry: ProviderCapabilityRegistry,
    ) -> None:
        if registry is None:
            raise ValueError("capability registry required")

        self.registry = registry
        self.bridge = ProviderCapabilityBridge(registry)
        self.resolver = ProviderCapabilityResolver(registry)

    def bind(
        self,
        providers: Tuple[Any, ...],
        provider_names: Optional[Tuple[str, ...]] = None,
        capabilities: Optional[Tuple[str, ...]] = None,
    ) -> None:
        if providers is None:
            raise ValueError("providers required")

        if provider_names is None:
            provider_names = tuple(
                getattr(p, "name", "") for p in providers
            )

        if len(provider_names) != len(providers):
            raise ValueError(
                "provider_names length mismatch: "
                f"{len(provider_names)} != {len(providers)}"
            )

        for provider, provider_name in zip(providers, provider_names):
            name = (provider_name or "").strip()
            if not name:
                name = getattr(provider, "name", "")
            if not name:
                raise ValueError(
                    "provider name required for capability binding"
                )
            self.bridge.bind(
                provider_name=name,
                provider=provider,
                capabilities=capabilities,
            )

    def ready(self) -> bool:
        return (
            self.registry.ready()
            and self.bridge.ready()
            and self.resolver.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registry": self.registry.dump(),
        }


__all__ = ["CapabilityAssembly"]
