from __future__ import annotations

from fastapi import FastAPI

from backend.api.http_entry.fastapi_http_runtime_entry_contract import (
    FastAPIHTTPRuntimeEntryContract,
)
from backend.api.http_entry.fastapi_http_runtime_entry_lifecycle_contract import (
    FastAPIHTTPRuntimeEntryLifecycleContract,
)
from backend.api.http_entry.fastapi_http_runtime_entry_support import (
    FastAPIHTTPRuntimeEntrySupport,
)


class FastAPIHTTPRuntimeEntry(
    FastAPIHTTPRuntimeEntryContract,
):
    """
    Canonical FastAPI HTTP runtime registration boundary.

    Owns only:
        - one lifecycle dependency
        - HTTP route registration
        - HTTP route cleanup
        - application-state projection
    """

    VERSION = "1.1"
    STATE_KEY = "fastapi_http_runtime_entry"

    def __init__(
        self,
        lifecycle: FastAPIHTTPRuntimeEntryLifecycleContract,
        support: FastAPIHTTPRuntimeEntrySupport | None = None,
    ) -> None:
        self.support = (
            support
            or FastAPIHTTPRuntimeEntrySupport()
        )
        self.lifecycle = (
            self.support.validate_lifecycle(
                lifecycle
            )
        )
        self.application: FastAPI | None = None
        self.started = False
        self.start_count = 0
        self.stop_count = 0

    def start(
        self,
        *,
        application: FastAPI,
        startup: object,
    ) -> None:
        application = (
            self.support.validate_application(
                application
            )
        )
        startup = self.support.validate_startup(
            startup
        )

        if self.started:
            if self.application is application:
                return

            raise RuntimeError(
                "http runtime entry already bound"
            )

        try:
            self.lifecycle.register(
                application,
                startup,
            )

            if not self.lifecycle.registered():
                raise RuntimeError(
                    "http runtime routes not registered"
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
                self.lifecycle.unregister(
                    application
                )
            finally:
                self.application = None
                self.started = False
            raise

    def stop(
        self,
        application: FastAPI | None = None,
    ) -> None:
        target = (
            application
            or self.application
        )

        if target is not None:
            self.lifecycle.unregister(
                target
            )

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

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.lifecycle.ready()
            and (
                not self.started
                or self.lifecycle.registered()
            )
        )

    def registered(
        self,
    ) -> bool:
        return (
            self.started
            and self.lifecycle.registered()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self.started,
            "registered": self.registered(),
            "start_count": self.start_count,
            "stop_count": self.stop_count,
            "lifecycle": self.lifecycle.dump(),
        }


__all__ = [
    "FastAPIHTTPRuntimeEntry",
]
