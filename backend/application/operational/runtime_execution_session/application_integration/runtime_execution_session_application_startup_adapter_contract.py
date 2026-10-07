from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimeExecutionSessionApplicationStartupAdapterContract(
    Protocol,
):
    """
    Structural contract consumed by ApplicationStartup.

    Owns:
        - application integration delegation
        - shutdown delegation
        - readiness projection
    """

    def start(
        self,
        *,
        context: dict[str, object],
        project_session_service: object,
    ) -> object:
        ...

    def stop(
        self,
        *,
        context: dict[str, object],
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
    "RuntimeExecutionSessionApplicationStartupAdapterContract",
]
