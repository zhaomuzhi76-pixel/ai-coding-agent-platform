from __future__ import annotations

from backend.process_runtime.process_runtime_entry import (
    ProcessRuntimeEntry,
)
from backend.process_runtime.process_runtime_entry_support import (
    ProcessRuntimeEntrySupport,
)


class ProcessRuntimeEntryFactory:
    """
    Construction boundary for the canonical process runtime entry.

    Owns only:
        - supervision validation
        - ProcessRuntimeEntry construction
        - readiness validation

    Does not own:
        - process application entry construction
        - process supervision construction
        - FastAPI construction
        - process main orchestration
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        supervision,
        support: ProcessRuntimeEntrySupport | None = None,
    ) -> ProcessRuntimeEntry:
        self._validate_supervision(
            supervision
        )

        entry = ProcessRuntimeEntry(
            supervision=supervision,
            support=support,
        )

        if not entry.ready():
            raise RuntimeError(
                "process runtime entry unavailable"
            )

        return entry

    @staticmethod
    def _validate_supervision(
        supervision,
    ) -> None:
        if supervision is None:
            raise ValueError(
                "process supervision required"
            )

        for name in (
            "run",
            "ready",
            "running",
            "failed",
            "dump",
        ):
            if not callable(
                getattr(
                    supervision,
                    name,
                    None,
                )
            ):
                raise TypeError(
                    "process supervision must expose "
                    f"{name}()"
                )

        if not supervision.ready():
            raise RuntimeError(
                "process supervision not ready"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessRuntimeEntryFactory",
]
