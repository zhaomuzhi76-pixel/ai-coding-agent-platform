from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessObservabilityContract(Protocol):
    """
    Process-level runtime observation contract.

    Owns only:
        - process control observation
        - health projection
        - failure projection
        - diagnostic snapshot

    Does not own:
        - process execution
        - runner construction
        - FastAPI construction
        - application lifecycle
        - signal registration
    """

    def snapshot(self) -> dict[str, object]:
        ...

    def healthy(self) -> bool:
        ...

    def failed(self) -> bool:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...
