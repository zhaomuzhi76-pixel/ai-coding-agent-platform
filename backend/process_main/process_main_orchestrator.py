from __future__ import annotations

from backend.process_main.process_main_orchestrator_contract import (
    ProcessMainOrchestratorContract,
)
from backend.process_main.process_main_orchestrator_support import (
    ProcessMainOrchestratorSupport,
)


class ProcessMainOrchestrator(
    ProcessMainOrchestratorContract,
):
    """
    Canonical top-level process execution orchestrator.

    Owns:
        - one injected ProcessRuntimeEntry
        - one top-level run boundary
        - final exit-code projection
        - orchestration state

    Does not own:
        - process runtime construction
        - supervision construction
        - application construction
        - application lifecycle
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        entry: object,
        support: (
            ProcessMainOrchestratorSupport
            | None
        ) = None,
    ) -> None:
        self.support = (
            support
            or ProcessMainOrchestratorSupport()
        )

        self.entry = (
            self.support.validate_runtime_entry(
                entry
            )
        )

        self._running = False
        self._failed = False
        self._exit_code: int | None = None
        self.run_count = 0

    def run(self) -> int:
        if self._running:
            raise RuntimeError(
                "process main orchestrator already running"
            )

        self._running = True
        self._failed = False
        self._exit_code = None
        self.run_count += 1

        try:
            result = self.entry.run()

            if not isinstance(
                result,
                int,
            ):
                raise TypeError(
                    "process runtime entry must return int"
                )

            self._exit_code = result
            return result

        except BaseException:
            self._failed = True
            self._exit_code = self.entry.dump().get(
                "exit_code"
            )
            raise

        finally:
            self._running = False

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.entry is not None
            and self.entry.ready()
        )

    def running(self) -> bool:
        return self._running

    def failed(self) -> bool:
        return self._failed

    def exit_code(self) -> int | None:
        return self._exit_code

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "running": self.running(),
            "failed": self.failed(),
            "exit_code": self.exit_code(),
            "run_count": self.run_count,
            "entry": self.entry.dump(),
        }


__all__ = [
    "ProcessMainOrchestrator",
]
