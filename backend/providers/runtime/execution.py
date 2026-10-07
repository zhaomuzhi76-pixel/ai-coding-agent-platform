from __future__ import annotations

from typing import Any, AsyncIterator

from backend.providers.runtime.contracts import (
    ProviderExecutionProtocol,
)


class ProviderExecutionCoordinator(
    ProviderExecutionProtocol,
):
    """
    Provider capability execution coordinator.

    It delegates actual capability execution to the
    registered provider capability resolver.
    """

    VERSION = "1.0"

    def __init__(
        self,
        resolver,
    ) -> None:
        if resolver is None:
            raise ValueError(
                "provider capability resolver required"
            )

        self.resolver = resolver
        self.execution_count = 0
        self.failure_count = 0

    async def chat(
        self,
        provider: str,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        return await self._execute(
            provider,
            "chat",
            messages,
            model=model,
            **kwargs,
        )

    def stream_chat(
        self,
        provider: str,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        return self._stream(
            provider,
            messages,
            model=model,
            **kwargs,
        )

    async def embedding(
        self,
        provider: str,
        texts: list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        return await self._execute(
            provider,
            "embedding",
            texts,
            model=model,
            **kwargs,
        )

    async def _execute(
        self,
        provider: str,
        capability: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        self.execution_count += 1

        try:
            return await self.resolver.execute(
                provider,
                capability,
                *args,
                **kwargs,
            )
        except Exception:
            self.failure_count += 1
            raise

    async def _stream(
        self,
        provider: str,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self.execution_count += 1

        try:
            stream = await self.resolver.execute(
                provider,
                "stream_chat",
                messages,
                model=model,
                **kwargs,
            )

            async for chunk in stream:
                yield chunk

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return self.resolver.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "ready": self.ready(),
        }


__all__ = [
    "ProviderExecutionCoordinator",
]
