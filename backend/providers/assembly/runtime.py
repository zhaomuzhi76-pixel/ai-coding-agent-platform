from __future__ import annotations

from typing import Any, AsyncIterator

from backend.providers.assembly.context import (
    ProviderAssemblyContext,
)


class ProviderAssemblyRuntime:
    """
    Stable runtime exposed by provider assembly.

    Delegates execution to ProviderRuntime.
    """

    VERSION = "1.0"

    def __init__(
        self,
        context: ProviderAssemblyContext,
    ) -> None:
        if context is None:
            raise ValueError(
                "provider assembly context required"
            )

        if not context.ready():
            raise RuntimeError(
                "provider assembly context not ready"
            )

        self.context = context
        self.runtime = context.runtime

    async def chat(
        self,
        provider: str | None,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        return await self.runtime.chat(
            provider,
            messages,
            model,
            **kwargs,
        )

    def stream_chat(
        self,
        provider: str | None,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        return self.runtime.stream_chat(
            provider,
            messages,
            model,
            **kwargs,
        )

    async def embedding(
        self,
        provider: str | None,
        texts: list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        return await self.runtime.embedding(
            provider,
            texts,
            model,
            **kwargs,
        )

    def ready(self) -> bool:
        return (
            self.context.ready()
            and self.runtime.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "context": self.context.dump(),
            "runtime": self.runtime.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ProviderAssemblyRuntime",
]
