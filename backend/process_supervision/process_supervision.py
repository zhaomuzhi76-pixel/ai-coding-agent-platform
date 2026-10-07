from __future__ import annotations

from backend.process_supervision.process_supervision_contract import (
    ProcessSupervisionContract,
)
from backend.process_supervision.process_supervision_support import (
    ProcessSupervisionSupport,
)


class ProcessSupervision(
    ProcessSupervisionContract,
):
    """
    Canonical process execution supervision boundary.

    Owns:
        - one injected process runner
        - one process-run state machine
        - exit-code normalization
        - failure projection

    Does not own:
        - application creation
        - application lifecycle
        - runner construction
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        runner,
        support: ProcessSupervisionSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProcessSupervisionSupport()
        )

        self.runner = (
            self.support.validate_runner(
                runner
            )
        )

        self._running = False
        self._failed = False
        self._exit_code: int | None = None
        self.start_count = 0
        self.finish_count = 0
        self.failure_count = 0

    def run(self) -> int:
        if self._running:
            raise RuntimeError(
                "process already running"
            )

        self._running = True
        self._failed = False
        self._exit_code = None
        self.start_count += 1

        try:
            result = self.runner()
            exit_code = (
                self.support.normalize_exit_code(
                    result
                )
            )

            self._exit_code = exit_code
            self.finish_count += 1
            return exit_code

        except BaseException as error:
            self._failed = True
            self.failure_count += 1
            self._exit_code = (
                self.support.normalize_exception(
                    error
                )
            )
            raise

        finally:
            self._running = False

    def ready(self) -> bool:
        return (
            self.support.ready()
            and callable(self.runner)
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
            "start_count": self.start_count,
            "finish_count": self.finish_count,
            "failure_count": self.failure_count,
        }


__all__ = [
    "ProcessSupervision",
]
