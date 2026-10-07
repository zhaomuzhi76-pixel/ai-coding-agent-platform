from __future__ import annotations

from backend.process_runtime.process_runtime_entry_contract import (
    ProcessRuntimeEntryContract,
)
from backend.process_runtime.process_runtime_entry_support import (
    ProcessRuntimeEntrySupport,
)


class ProcessRuntimeEntry(ProcessRuntimeEntryContract):
    """
    Canonical process runtime delegation boundary.

    Owns:
        - one injected process supervision
        - runtime invocation delegation
        - runtime readiness projection
        - diagnostics

    Does not own:
        - process lifecycle state
        - exit-code normalization
        - process runner
        - supervision construction
    """

    VERSION = "2.0"

    def __init__(
        self,
        *,
        supervision: object,
        support: ProcessRuntimeEntrySupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProcessRuntimeEntrySupport()
        )
        self.supervision = (
            self.support.validate_supervision(
                supervision
            )
        )
        self.run_count = 0

    def run(self) -> int:
        self.run_count += 1

        result = self.supervision.run()

        if not isinstance(
            result,
            int,
        ):
            raise TypeError(
                "process supervision must return int"
            )

        return result

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.supervision.ready()
        )

    def running(self) -> bool:
        return self.supervision.running()

    def failed(self) -> bool:
        return self.supervision.failed()

    def exit_code(self) -> int | None:
        return self.supervision.exit_code()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "running": self.running(),
            "failed": self.failed(),
            "exit_code": self.exit_code(),
            "run_count": self.run_count,
            "supervision": self.supervision.dump(),
        }


__all__ = [
    "ProcessRuntimeEntry",
]
