from __future__ import annotations

from backend.process_operations.process_operations_contract import (
    ProcessOperationsContract,
)
from backend.process_operations.process_operations_support import (
    ProcessOperationsSupport,
)


class ProcessOperations(
    ProcessOperationsContract,
):
    """
    Canonical aggregate process operations boundary.

    Owns only:
        - one control dependency
        - one observability dependency
        - one health dependency
        - unified operational projection

    Does not own:
        - process execution
        - process construction
        - lower-layer lifecycle control
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        control: object,
        observability: object,
        health: object,
        support: ProcessOperationsSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProcessOperationsSupport()
        )

        self.control = (
            self.support.validate_control(
                control
            )
        )
        self.observability = (
            self.support.validate_observability(
                observability
            )
        )
        self.health = (
            self.support.validate_health(
                health
            )
        )

        self.snapshot_count = 0

    def healthy(self) -> bool:
        return (
            bool(self.health.healthy())
            and bool(
                self.observability.healthy()
            )
        )

    def ready(self) -> bool:
        return (
            self.support.ready()
            and bool(self.control.ready())
            and bool(self.observability.ready())
            and bool(self.health.ready())
        )

    def running(self) -> bool:
        return bool(
            self.control.running()
        )

    def failed(self) -> bool:
        return (
            bool(self.control.failed())
            or bool(self.observability.failed())
            or bool(self.health.failed())
        )

    def status(self) -> str:
        return self.snapshot()["status"]

    def snapshot(self) -> dict[str, object]:
        self.snapshot_count += 1

        running = self.running()
        failed = self.failed()
        healthy = self.healthy()

        return {
            "status": self.support.project_status(
                running=running,
                failed=failed,
                healthy=healthy,
            ),
            "running": running,
            "failed": failed,
            "healthy": healthy,
            "exit_code": self.control.exit_code(),
            "signal": self.control.signal(),
            "health": self.health.snapshot(),
            "observability": self.observability.snapshot(),
        }

    def dump(self) -> dict[str, object]:
        snapshot = self.snapshot()

        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "healthy": self.healthy(),
            "running": self.running(),
            "failed": self.failed(),
            "status": snapshot["status"],
            "snapshot_count": self.snapshot_count,
            "snapshot": snapshot,
            "control": self.control.dump(),
        }


__all__ = [
    "ProcessOperations",
]
