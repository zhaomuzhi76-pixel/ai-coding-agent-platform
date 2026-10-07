from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessApplicationEntryContract(
    Protocol,
):
    """
    Process-level public entry contract.

    Owns:
        - canonical FastAPI application projection
        - process runner delegation
        - readiness projection
        - diagnostics

    Does not own:
        - FastAPI construction
        - ApplicationStartup construction
        - runtime construction
        - HTTP route construction
        - WebSocket route construction
        - lifecycle implementation
    """

    def application(self) -> object:
        ...

    def start(self) -> int:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...
