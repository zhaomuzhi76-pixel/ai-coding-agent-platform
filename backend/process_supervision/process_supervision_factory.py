from __future__ import annotations

from backend.process_supervision.process_supervision import (
    ProcessSupervision,
)
from backend.process_supervision.process_supervision_support import (
    ProcessSupervisionSupport,
)


class ProcessSupervisionFactory:
    """
    Construction boundary for canonical process supervision.

    Owns only:
        - process application entry validation
        - runner extraction
        - ProcessSupervision construction
        - readiness validation

    Does not own:
        - process application entry construction
        - FastAPI construction
        - process runtime construction
        - process main orchestration
    """

    VERSION = "3.1"

    def create(
        self,
        *,
        entry,
        support: ProcessSupervisionSupport | None = None,
    ) -> ProcessSupervision:
        self._validate_entry(entry)

        runner = self._resolve_runner(entry)

        supervision = ProcessSupervision(
            runner=runner,
            support=support,
        )

        if not supervision.ready():
            raise RuntimeError(
                "process supervision unavailable"
            )

        return supervision

    @staticmethod
    def _validate_entry(entry) -> None:
        if entry is None:
            raise ValueError(
                "process application entry required"
            )

        ready = getattr(
            entry,
            "ready",
            None,
        )

        if not callable(ready):
            raise TypeError(
                "process application entry must expose ready()"
            )

        if not bool(ready()):
            raise RuntimeError(
                "process application entry not ready"
            )

    @staticmethod
    def _resolve_runner(entry):
        start = getattr(
            entry,
            "start",
            None,
        )

        if not callable(start):
            raise TypeError(
                "process application entry must expose start()"
            )

        return start

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessSupervisionFactory",
]
