from __future__ import annotations

from typing import Any, AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class ApplicationProviderRuntimeProtocol(
    Protocol,
):
    async def chat(
        self,
        provider: str,
        messages: list[dict],
        model: str,
        **kwargs: Any,
    ) -> str:
        ...

    def stream_chat(
        self,
        provider: str,
        messages: list[dict],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        ...

    async def embedding(
        self,
        provider: str,
        texts: list[str],
        model: str,
        **kwargs: Any,
    ) -> list[list[float]]:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class ApplicationProviderGatewayProtocol(
    Protocol,
):
    async def chat(
        self,
        provider: str,
        messages: list[dict],
        model: str,
        **kwargs: Any,
    ) -> str:
        ...

    def stream_chat(
        self,
        provider: str,
        messages: list[dict],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        ...

    async def embedding(
        self,
        provider: str,
        texts: list[str],
        model: str,
        **kwargs: Any,
    ) -> list[list[float]]:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationProviderGatewayProtocol",
    "ApplicationProviderRuntimeProtocol",
]
