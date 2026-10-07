from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessRuntimeEntryContract(
    Protocol,
):
    """
    Process runtime entry contract.

    Owns only:
        - one process supervision dependency
        - process execution delegation
        - execution state projection
        - diagnostics

    Does not own:
        - FastAPI construction
        - application lifecycle construction
        - process supervision construction
        - business execution
    """

    def run(self) -> int:
        ...

    def ready(self) -> bool:
        ...

    def running(self) -> bool:
        ...

    def failed(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...
