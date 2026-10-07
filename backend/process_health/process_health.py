from __future__ import annotations

from backend.process_health.process_health_contract import (
    ProcessHealthContract,
)
from backend.process_health.process_health_support import (
    ProcessHealthSupport,
)


class ProcessHealth(
    ProcessHealthContract,
):
    """
    Canonical process health/readiness projection.

    Owns only:
        - one process observability dependency
        - health/readiness projection
        - status projection
        - diagnostics

    Does not own:
        - process control
        - process execution
        - process supervision
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        observability: object,
        support: ProcessHealthSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProcessHealthSupport()
        )

        self.observability = (
            self.support.validate_observability(
                observability
            )
        )

        self.snapshot_count = 0

    def healthy(self) -> bool:
        return bool(
            self.observability.healthy()
        )

    def ready(self) -> bool:
        return (
            self.support.ready()
            and bool(
                self.observability.ready()
            )
        )

    def failed(self) -> bool:
        return bool(
            self.observability.failed()
        )

    def status(self) -> str:
        snapshot = self.snapshot()
        return self.support.project_status(
            snapshot
        )

    def snapshot(self) -> dict[str, object]:
        self.snapshot_count += 1

        snapshot = self.support.normalize_snapshot(
            self.observability.snapshot()
        )

        return {
            **snapshot,
            "status": self.support.project_status(
                snapshot
            ),
        }

    def dump(self) -> dict[str, object]:
        snapshot = self.snapshot()

        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "healthy": self.healthy(),
            "failed": self.failed(),
            "status": snapshot["status"],
            "snapshot_count": self.snapshot_count,
            "snapshot": snapshot,
            "observability": self.observability.dump(),
        }


__all__ = [
    "ProcessHealth",
]
