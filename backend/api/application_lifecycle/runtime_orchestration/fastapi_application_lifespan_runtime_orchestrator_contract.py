from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FastAPIApplicationLifespanRuntimeOrchestratorContract(
    Protocol,
):
    """
    Canonical ApplicationLifespan orchestration contract.

    Owns:
        - ordered startup of already-built upper integrations
        - reverse-order shutdown
        - startup rollback
        - readiness projection
        - diagnostics

    Does not own:
        - ApplicationStartup construction
        - HTTP route construction
        - WebSocket execution
        - project-session business implementation
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

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "FastAPIApplicationLifespanRuntimeOrchestratorContract",
]
