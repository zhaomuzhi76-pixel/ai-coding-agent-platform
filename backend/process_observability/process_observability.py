from __future__ import annotations

from backend.process_observability.process_observability_contract import (
    ProcessObservabilityContract,
)
from backend.process_observability.process_observability_support import (
    ProcessObservabilitySupport,
)


class ProcessObservability(
    ProcessObservabilityContract,
):
    """
    Canonical process-level runtime observation boundary.

    Owns only:
        - observation of frozen ProcessControl
        - health projection
        - failure projection
        - diagnostic snapshot
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        control: object,
        support: ProcessObservabilitySupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProcessObservabilitySupport()
        )

        self.control = (
            self.support.validate_control(
                control
            )
        )

        self.snapshot_count = 0

    def snapshot(self) -> dict[str, object]:
        self.snapshot_count += 1

        return {
            "state": self.support.project_state(
                self.control
            ),
            "healthy": self.healthy(),
            "failed": self.failed(),
            "running": bool(
                self.control.running()
            ),
            "exit_code": self.control.exit_code(),
            "signal": self.control.signal(),
        }

    def healthy(self) -> bool:
        return self.support.project_health(
            self.control
        )

    def failed(self) -> bool:
        return bool(
            self.control.failed()
        )

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.control.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "healthy": self.healthy(),
            "failed": self.failed(),
            "snapshot_count": self.snapshot_count,
            "snapshot": self.snapshot(),
            "control": self.control.dump(),
        }


__all__ = [
    "ProcessObservability",
]
