from __future__ import annotations

from backend.application.modules.runtime_llm_provider_adapter import (
    RuntimeLLMProviderAdapter,
)
from backend.application.provider_gateway import (
    ApplicationProviderGatewayProtocol,
)


class RuntimeLLMProviderAdapterFactory:
    """
    Sole construction owner for RuntimeLLMProviderAdapter.
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        provider: ApplicationProviderGatewayProtocol,
    ) -> RuntimeLLMProviderAdapter:
        if not self.ready():
            raise RuntimeError(
                "runtime llm adapter factory unavailable"
            )

        if provider is None:
            raise ValueError(
                "provider gateway required"
            )

        adapter = RuntimeLLMProviderAdapter(
            provider
        )

        if not adapter.ready():
            raise RuntimeError(
                "runtime llm provider adapter unavailable"
            )

        return adapter

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeLLMProviderAdapterFactory",
]
