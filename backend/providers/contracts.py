from __future__ import annotations

from typing import Any, AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class ProviderProtocol(Protocol):
    """
    Runtime-registered provider execution contract.

    Concrete providers expose stable identity plus their external
    model execution operations. Provider construction is owned by
    ProviderFactory and lifecycle teardown remains outside this
    registration contract.
    """

    name: str
    version: str
    category: str

    def chat(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        ...

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        ...

    def embedding(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class ProviderFactoryProtocol(Protocol):
    """
    Provider construction registry contract.
    """

    def register(
        self,
        provider_type: str,
        provider_class: type[Any],
    ) -> None:
        ...

    def create(
        self,
        provider_type: str,
        **kwargs: Any,
    ) -> Any:
        ...

    def exists(
        self,
        provider_type: str,
    ) -> bool:
        ...

    def list_types(self) -> list[str]:
        ...

    def clear(self) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ProviderProtocol",
    "ProviderFactoryProtocol",
]
