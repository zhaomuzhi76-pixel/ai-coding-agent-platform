from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FastAPIHTTPEntryLifespanIntegrationContract(
    Protocol,
):
    """
    Structural bridge between FastAPI application lifespan and
    the frozen FastAPI HTTP runtime entry.

    Owns:
        - HTTP entry startup delegation
        - HTTP entry shutdown delegation
        - readiness projection
        - registration state projection

    Does not own:
        - HTTP route construction
        - application startup construction
        - runtime construction
        - submission execution
    """

    def start(
        self,
        *,
        application: object,
        startup: object,
    ) -> None:
        ...

    def stop(
        self,
        application: object,
    ) -> None:
        ...

    def ready(self) -> bool:
        ...

    def registered(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "FastAPIHTTPEntryLifespanIntegrationContract",
]
