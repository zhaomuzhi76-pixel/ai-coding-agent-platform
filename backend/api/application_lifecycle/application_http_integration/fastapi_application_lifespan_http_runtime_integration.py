from __future__ import annotations

import inspect

from backend.api.application_lifecycle.application_http_integration.fastapi_application_lifespan_http_runtime_integration_contract import (
    FastAPIApplicationLifespanHTTPRuntimeIntegrationContract,
)
from backend.api.application_lifecycle.application_http_integration.fastapi_application_lifespan_http_runtime_integration_support import (
    FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport,
)


class FastAPIApplicationLifespanHTTPRuntimeIntegration(
    FastAPIApplicationLifespanHTTPRuntimeIntegrationContract,
):
    """
    Application-lifespan bridge for the frozen HTTP runtime entry.

    Owns:
        - lower HTTP entry lifecycle delegation
        - real registration verification
        - application state projection

    Does not own:
        - FastAPI construction
        - route construction
        - ApplicationStartup construction
        - submission execution
    """

    VERSION = "1.6"
    CONTEXT_KEY = (
        "application_lifespan_http_runtime_integration"
    )

    def __init__(
        self,
        entry: object,
        support: (
            FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport
            | None
        ) = None,
    ) -> None:
        self.support = (
            support
            or FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport()
        )
        self.entry = self.support.validate_entry(entry)
        self.application = None
        self.started = False
        self.start_count = 0
        self.stop_count = 0

    async def start(
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
                "application HTTP runtime integration already bound"
            )

        try:
            result = self.entry.start(
                application=application,
                startup=startup,
            )

            await self._await_if_needed(result)

            if not self.support.registration_valid(
                self.entry,
                application,
            ):
                raise RuntimeError(
                    self.support.registration_error(
                        self.entry,
                        application,
                    )
                )

            self.application = application
            self.started = True
            self.start_count += 1

            setattr(
                application.state,
                self.CONTEXT_KEY,
                self,
            )
        except Exception:
            await self._stop_entry(
                application
            )
            self._clear_state(
                application
            )
            self.application = None
            self.started = False
            raise

    async def stop(
        self,
        application: object,
    ) -> None:
        application = self.support.validate_application(
            application
        )
        target = self.application or application

        try:
            await self._stop_entry(
                target
            )
        finally:
            self._clear_state(
                target
            )

            if self.started:
                self.stop_count += 1

            self.application = None
            self.started = False

    def registered(
        self,
    ) -> bool:
        if not self.started:
            return False

        if self.application is None:
            return False

        return self.support.registration_valid(
            self.entry,
            self.application,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.entry.ready()
            and (
                not self.started
                or self.registered()
            )
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
            "context_key": self.CONTEXT_KEY,
            "entry": self.entry.dump(),
        }

    async def _stop_entry(
        self,
        application,
    ) -> None:
        result = self.entry.stop(
            application
        )
        await self._await_if_needed(
            result
        )

    @staticmethod
    async def _await_if_needed(
        result,
    ) -> None:
        if inspect.isawaitable(result):
            await result

    def _clear_state(
        self,
        application,
    ) -> None:
        current = getattr(
            application.state,
            self.CONTEXT_KEY,
            None,
        )

        if current is self:
            delattr(
                application.state,
                self.CONTEXT_KEY,
            )


__all__ = [
    "FastAPIApplicationLifespanHTTPRuntimeIntegration",
]
