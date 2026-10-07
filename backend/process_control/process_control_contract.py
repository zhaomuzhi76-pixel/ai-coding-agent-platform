from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessControlContract(Protocol):
    """
    Final OS-process control boundary.

    Owns only:
        - process-main delegation
        - signal observation
        - exit-code projection
        - failure projection
        - diagnostics

    Does not own:
        - FastAPI construction
        - application lifespan
        - runtime construction
        - supervision construction
        - process-main construction
    """

    def run(self) -> int:
        ...

    def ready(self) -> bool:
        ...

    def running(self) -> bool:
        ...

    def failed(self) -> bool:
        ...

    def exit_code(self) -> int | None:
        ...

    def signal(self) -> int | None:
        ...

    def dump(self) -> dict[str, object]:
        ...
