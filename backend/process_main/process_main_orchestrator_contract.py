from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessMainOrchestratorContract(
    Protocol,
):
    """
    Top-level process main orchestration contract.

    Owns only:
        - one process runtime entry
        - one process execution delegation
        - final exit-code projection
        - readiness and diagnostics

    Does not own:
        - FastAPI construction
        - application lifecycle
        - process supervision construction
        - runtime entry construction
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

    def exit_code(self) -> int | None:
        ...

    def dump(self) -> dict[str, object]:
        ...
