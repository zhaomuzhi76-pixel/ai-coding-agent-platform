from __future__ import annotations

from typing import Any, AsyncIterator

from backend.providers.runtime.contracts import (
    ProviderExecutionProtocol,
    ProviderSelectionProtocol,
)


class ProviderRuntime:
    """
    Stable provider runtime facade.

    Provider and model selection are request-owned.
    No provider/model fallback is performed here.
    """

    VERSION = "2.0"

    def __init__(
        self,
        selector: ProviderSelectionProtocol,
        execution: ProviderExecutionProtocol,
    ) -> None:
        if selector is None:
            raise ValueError(
                "provider selector required"
            )
        if execution is None:
            raise ValueError(
                "provider execution required"
            )

        self.selector = selector
        self.execution = execution

    async def chat(
        self,
        provider: str,
        messages: list[dict],
        model: str,
        **kwargs: Any,
    ) -> str:
        selected = self.selector.select(
            provider
        )
        return await self.execution.chat(
            selected,
            messages,
            model,
            **kwargs,
        )

    def stream_chat(
        self,
        provider: str,
        messages: list[dict],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        selected = self.selector.select(
            provider
        )
        return self.execution.stream_chat(
            selected,
            messages,
            model,
            **kwargs,
        )

    async def embedding(
        self,
        provider: str,
        texts: list[str],
        model: str,
        **kwargs: Any,
    ) -> list[list[float]]:
        selected = self.selector.select(
            provider
        )
        return await self.execution.embedding(
            selected,
            texts,
            model,
            **kwargs,
        )

    def ready(self) -> bool:
        return (
            self.selector.ready()
            and self.execution.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "selector": self.selector.dump(),
            "execution": self.execution.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ProviderRuntime",
]
