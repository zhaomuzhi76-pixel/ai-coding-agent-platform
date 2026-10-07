from __future__ import annotations
from backend.config.constants.endpoints import (
    BACKEND_PORT,
)

from typing import Callable

from backend.process_entry.process_application_entry import (
    ProcessApplicationEntry,
)
from backend.process_entry.process_application_entry_support import (
    ProcessApplicationEntrySupport,
)


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = BACKEND_PORT
DEFAULT_LOG_LEVEL = "info"


class ProcessApplicationEntryFactory:
    """
    Construction boundary for the canonical process application entry.

    Owns:
        - injected application validation
        - runner resolution
        - process entry configuration
        - process entry construction

    Does not own:
        - FastAPI construction
        - application lifecycle construction
        - supervision
        - runtime orchestration
        - top-level application discovery
    """

    VERSION = "1.3"

    def create(
        self,
        *,
        application: object,
        runner: Callable | None = None,
        host: str | None = None,
        port: int | None = None,
        log_level: str | None = None,
        support: (
            ProcessApplicationEntrySupport
            | None
        ) = None,
    ) -> ProcessApplicationEntry:
        if application is None:
            raise ValueError(
                "application required"
            )

        if runner is None:
            import uvicorn

            runner = uvicorn.run

        active_host = (
            host
            if host is not None
            else DEFAULT_HOST
        )

        active_port = (
            port
            if port is not None
            else DEFAULT_PORT
        )

        active_log_level = (
            log_level
            if log_level is not None
            else DEFAULT_LOG_LEVEL
        )

        entry = ProcessApplicationEntry(
            application=application,
            runner=runner,
            host=active_host,
            port=active_port,
            log_level=active_log_level,
            support=support,
        )

        if not entry.ready():
            raise RuntimeError(
                "process application entry unavailable"
            )

        return entry

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
            "default_host": DEFAULT_HOST,
            "default_port": DEFAULT_PORT,
            "default_log_level": DEFAULT_LOG_LEVEL,
        }


__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_LOG_LEVEL",
    "ProcessApplicationEntryFactory",
]
