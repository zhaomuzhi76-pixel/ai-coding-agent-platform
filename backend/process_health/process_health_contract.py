from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessHealthContract(Protocol):
    """
    Process health and readiness contract.

    Owns only:
        - process health projection
        - process readiness projection
        - failure-state projection
        - diagnostic snapshot

    Does not own:
        - process execution
        - process control
        - process supervision
        - FastAPI construction
        - application lifecycle
    """

    def healthy(self) -> bool:
        ...

    def ready(self) -> bool:
        ...

    def failed(self) -> bool:
        ...

    def status(self) -> str:
        ...

    def snapshot(self) -> dict[str, object]:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ProcessHealthContract",
]
