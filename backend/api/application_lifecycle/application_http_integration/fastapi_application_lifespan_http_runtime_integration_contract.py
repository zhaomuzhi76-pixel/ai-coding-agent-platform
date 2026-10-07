from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FastAPIApplicationLifespanHTTPRuntimeIntegrationContract(
    Protocol,
):
    """
    ApplicationLifespan-owned HTTP lifecycle orchestration contract.

    Owns only:
        - application HTTP integration lifecycle delegation
        - registration projection
        - readiness projection
        - diagnostics
    """

    async def start(
        self,
        *,
        application: object,
        startup: object,
    ) -> None:
        ...

    async def stop(
        self,
        application: object,
    ) -> None:
        ...

    def registered(self) -> bool:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "FastAPIApplicationLifespanHTTPRuntimeIntegrationContract",
]
