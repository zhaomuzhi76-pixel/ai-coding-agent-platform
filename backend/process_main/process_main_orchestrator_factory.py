from __future__ import annotations

from typing import Callable

from backend.process_entry.process_application_entry import (
    ProcessApplicationEntry,
)
from backend.process_entry.process_application_entry_factory import (
    ProcessApplicationEntryFactory,
)
from backend.process_main.process_main_orchestrator import (
    ProcessMainOrchestrator,
)
from backend.process_main.process_main_orchestrator_support import (
    ProcessMainOrchestratorSupport,
)
from backend.process_runtime.process_runtime_entry_factory import (
    ProcessRuntimeEntryFactory,
)
from backend.process_supervision.process_supervision_factory import (
    ProcessSupervisionFactory,
)


class ProcessMainOrchestratorFactory:
    """
    Sole construction owner for the top-level process chain.

    Owns:
        - injected process application entry resolution
        - process supervision resolution
        - process runtime entry resolution
        - ProcessMainOrchestrator construction

    Does not own:
        - FastAPI construction
        - top-level application discovery
        - application lifecycle construction
        - supervision implementation
        - runtime implementation
    """

    VERSION = "2.1"

    def create(
        self,
        *,
        entry: ProcessApplicationEntry | None = None,
        application: object | None = None,
        runner: Callable | None = None,
        supervision=None,
        support: (
            ProcessMainOrchestratorSupport
            | None
        ) = None,
    ) -> ProcessMainOrchestrator:
        active_application_entry = entry

        if active_application_entry is None:
            if application is None:
                raise ValueError(
                    "application required"
                )

            active_application_entry = (
                ProcessApplicationEntryFactory()
                .create(
                    application=application,
                    runner=runner,
                )
            )

        active_supervision = supervision

        if active_supervision is None:
            active_supervision = (
                ProcessSupervisionFactory()
                .create(
                    entry=active_application_entry,
                )
            )

        runtime_entry = (
            ProcessRuntimeEntryFactory()
            .create(
                supervision=active_supervision,
            )
        )

        orchestrator = ProcessMainOrchestrator(
            entry=runtime_entry,
            support=support,
        )

        if not orchestrator.ready():
            raise RuntimeError(
                "process main orchestrator unavailable"
            )

        return orchestrator

    def run(
        self,
        *,
        entry: ProcessApplicationEntry | None = None,
        application: object | None = None,
        runner: Callable | None = None,
        supervision=None,
    ) -> int:
        orchestrator = self.create(
            entry=entry,
            application=application,
            runner=runner,
            supervision=supervision,
        )

        return orchestrator.run()

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
    "ProcessMainOrchestratorFactory",
]
