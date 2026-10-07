from __future__ import annotations

from fastapi import FastAPI

from backend.process_entry.process_application_entry_contract import (
    ProcessApplicationEntryContract,
)
from backend.process_entry.process_application_entry_support import (
    ProcessApplicationEntrySupport,
)


class ProcessApplicationEntry(
    ProcessApplicationEntryContract,
):
    """
    Canonical process-level FastAPI entry.

    Owns only:
        - canonical application reference
        - process runner configuration
        - runner delegation
        - readiness and diagnostics
    """

    VERSION = "1.1"

    def __init__(
        self,
        *,
        application: FastAPI,
        runner,
        host: str,
        port: int,
        log_level: str,
        support: (
            ProcessApplicationEntrySupport
            | None
        ) = None,
    ) -> None:
        self.support = (
            support
            or ProcessApplicationEntrySupport()
        )

        self._application = (
            self.support.validate_application(
                application
            )
        )

        self._runner = (
            self.support.validate_runner(
                runner
            )
        )

        self.host = (
            self.support.validate_host(
                host
            )
        )

        self.port = (
            self.support.validate_port(
                port
            )
        )

        self.log_level = (
            self.support.validate_log_level(
                log_level
            )
        )

        self.start_count = 0

    def application(self) -> FastAPI:
        return self._application

    @property
    def runner(self):
        return self._runner

    def start(self) -> int:
        if not self.ready():
            raise RuntimeError(
                "process application entry unavailable"
            )

        self.start_count += 1

        result = self._runner(
            self._application,
            host=self.host,
            port=self.port,
            log_level=self.log_level,
        )

        if result is None:
            return 0

        if not isinstance(
            result,
            int,
        ):
            raise TypeError(
                "process runner must return int or None"
            )

        return result

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self._application is not None
            and callable(self._runner)
            and bool(self.host)
            and self.port > 0
            and bool(self.log_level)
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "start_count": self.start_count,
            "application": type(
                self._application
            ).__name__,
            "runner": getattr(
                self._runner,
                "__name__",
                type(self._runner).__name__,
            ),
        }


__all__ = [
    "ProcessApplicationEntry",
]
