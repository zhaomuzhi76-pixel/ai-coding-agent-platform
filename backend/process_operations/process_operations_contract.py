from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessOperationsContract(Protocol):
    """
    Process operational aggregate contract.

    Owns only:
        - control observation
        - health observation
        - operational state projection
        - unified diagnostics

    Does not own:
        - process execution
        - process supervision
        - process construction
        - FastAPI construction
        - application lifecycle
    """

    def healthy(self) -> bool:
        ...

    def ready(self) -> bool:
        ...

    def running(self) -> bool:
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
    "ProcessOperationsContract",
]
