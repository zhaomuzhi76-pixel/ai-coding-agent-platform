from __future__ import annotations

import signal
from types import FrameType

from backend.process_control.process_control_contract import (
    ProcessControlContract,
)
from backend.process_control.process_control_support import (
    ProcessControlSupport,
)


class ProcessControl(
    ProcessControlContract,
):
    """
    Final top-level process control boundary.

    Owns:
        - one process-main runner
        - process running state
        - signal observation
        - exit-code projection
        - failure projection
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        runner,
        support: ProcessControlSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProcessControlSupport()
        )
        self.runner = (
            self.support.validate_runner(
                runner
            )
        )
        self._running = False
        self._failed = False
        self._exit_code: int | None = None
        self._signal: int | None = None
        self.run_count = 0
        self.failure_count = 0

    def run(self) -> int:
        if self._running:
            raise RuntimeError(
                "process control already running"
            )

        self._running = True
        self._failed = False
        self._exit_code = None
        self._signal = None
        self.run_count += 1

        try:
            result = self.runner()
            self._exit_code = (
                self.support.normalize_result(
                    result
                )
            )
            return self._exit_code

        except BaseException as error:
            self._failed = True
            self.failure_count += 1
            self._exit_code = (
                self.support.normalize_exception(
                    error
                )
            )

            if isinstance(
                error,
                KeyboardInterrupt,
            ):
                self._signal = signal.SIGINT

            raise

        finally:
            self._running = False

    def handle_signal(
        self,
        signum: int,
        frame: FrameType | None = None,
    ) -> None:
        self._signal = (
            self.support.normalize_signal(
                signum
            )
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and callable(self.runner)
        )

    def running(
        self,
    ) -> bool:
        return self._running

    def failed(
        self,
    ) -> bool:
        return self._failed

    def exit_code(
        self,
    ) -> int | None:
        return self._exit_code

    def signal(
        self,
    ) -> int | None:
        return self._signal

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "running": self.running(),
            "failed": self.failed(),
            "exit_code": self.exit_code(),
            "signal": self.signal(),
            "signal_name": (
                self.support.signal_name(
                    self.signal()
                )
            ),
            "run_count": self.run_count,
            "failure_count": self.failure_count,
        }


__all__ = [
    "ProcessControl",
]
