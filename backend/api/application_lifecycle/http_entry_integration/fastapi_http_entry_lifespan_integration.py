from __future__ import annotations

from fastapi import FastAPI

from backend.api.application_lifecycle.http_entry_integration.fastapi_http_entry_lifespan_integration_contract import (
    FastAPIHTTPEntryLifespanIntegrationContract,
)
from backend.api.application_lifecycle.http_entry_integration.fastapi_http_entry_lifespan_integration_support import (
    FastAPIHTTPEntryLifespanIntegrationSupport,
)
from backend.api.http_entry.fastapi_http_runtime_entry import (
    FastAPIHTTPRuntimeEntry,
)


class FastAPIHTTPEntryLifespanIntegration(
    FastAPIHTTPEntryLifespanIntegrationContract,
):
    """
    Lifespan integration boundary for the frozen HTTP runtime entry.

    Owns:
        - one HTTP entry dependency
        - startup delegation
        - shutdown delegation
        - registration state

    Does not own:
        - route construction
        - submission lifecycle implementation
        - runtime construction
        - application bootstrap
    """

    VERSION = "1.0"
    STATE_KEY = "fastapi_http_entry_lifespan_integration"

    def __init__(
        self,
        entry: FastAPIHTTPRuntimeEntry,
        support: (
            FastAPIHTTPEntryLifespanIntegrationSupport
            | None
        ) = None,
    ) -> None:
        self.support = (
            support
            or FastAPIHTTPEntryLifespanIntegrationSupport()
        )
        self.entry = self.support.validate_entry(
            entry
        )
        self.application: FastAPI | None = None
        self.started = False
        self.start_count = 0
        self.stop_count = 0

    def start(
        self,
        *,
        application: object,
        startup: object,
    ) -> None:
        application = self.support.validate_application(
            application
        )
        startup = self.support.validate_startup(
            startup
        )

        if self.started:
            if self.application is application:
                return

            raise RuntimeError(
                "http lifespan integration already bound"
            )

        try:
            self.entry.start(
                application=application,
                startup=startup,
            )

            if not self.entry.registered():
                raise RuntimeError(
                    "http runtime entry not registered"
                )

            self.application = application
            self.started = True
            self.start_count += 1

            setattr(
                application.state,
                self.STATE_KEY,
                self,
            )
        except Exception:
            try:
                self.entry.stop(
                    application
                )
            finally:
                self.application = None
                self.started = False
            raise

    def stop(
        self,
        application: object,
    ) -> None:
        application = self.support.validate_application(
            application
        )

        target = self.application or application

        try:
            self.entry.stop(
                target
            )
        finally:
            current = getattr(
                target.state,
                self.STATE_KEY,
                None,
            )

            if current is self:
                delattr(
                    target.state,
                    self.STATE_KEY,
                )

            if self.started:
                self.stop_count += 1

            self.application = None
            self.started = False

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.entry.ready()
            and (
                not self.started
                or self.entry.registered()
            )
        )

    def registered(self) -> bool:
        return (
            self.started
            and self.entry.registered()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self.started,
            "registered": self.registered(),
            "start_count": self.start_count,
            "stop_count": self.stop_count,
            "entry": self.entry.dump(),
        }


__all__ = [
    "FastAPIHTTPEntryLifespanIntegration",
]
