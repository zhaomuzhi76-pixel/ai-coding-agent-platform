from __future__ import annotations

from backend.application.provider_gateway import (
    ApplicationProviderGatewayProtocol,
)
from backend.core.execution.llm_execution_contract import (
    LLMExecutionProviderProtocol,
)


class RuntimeLLMProviderAdapter(
    LLMExecutionProviderProtocol,
):
    """
    Application-to-runtime LLM provider adapter.

    Runtime-specific implementation details remain outside this
    Application boundary; the shared execution contract lives in Core.
    """

    VERSION = "2.0"

    def __init__(
        self,
        provider: ApplicationProviderGatewayProtocol,
    ) -> None:
        if provider is None:
            raise ValueError(
                "provider gateway required"
            )

        if not isinstance(
            provider,
            LLMExecutionProviderProtocol,
        ):
            raise TypeError(
                "provider gateway does not satisfy "
                "LLM execution contract"
            )

        self.provider = provider

    async def chat(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: object,
    ) -> object:
        return await self.provider.chat(
            provider=provider,
            model=model,
            messages=messages,
            **kwargs,
        )

    def ready(
        self,
    ) -> bool:
        return self.provider.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeLLMProviderAdapter",
]
