from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApplicationModuleProtocol(Protocol):
    """
    Application module contract.

    Owns:
        - module identity
        - module lifecycle boundary
        - module resolution
        - module context projection

    Does not own:
        - module construction
        - registry ownership
        - application startup
    """

    @property
    def name(
        self,
    ) -> str:
        ...

    @property
    def version(
        self,
    ) -> str:
        ...

    def start(
        self,
    ) -> None:
        ...

    def stop(
        self,
    ) -> None:
        ...

    def build(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        ...

    def resolve(
        self,
        name: str | None = None,
    ) -> Any:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationModuleProtocol",
]
