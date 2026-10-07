from __future__ import annotations

from backend.api.application_lifecycle.application_http_integration.fastapi_application_lifespan_http_runtime_integration import (
    FastAPIApplicationLifespanHTTPRuntimeIntegration,
)
from backend.api.application_lifecycle.application_http_integration.fastapi_application_lifespan_http_runtime_integration_support import (
    FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport,
)
from backend.api.application_lifecycle.http_entry_integration.fastapi_http_entry_lifespan_integration_factory import (
    FastAPIHTTPEntryLifespanIntegrationFactory,
)


class FastAPIApplicationLifespanHTTPRuntimeIntegrationFactory:
    """
    Construction boundary for the application-lifespan HTTP runtime
    integration.

    Owns:
        - lower HTTP lifecycle integration construction
        - top integration construction
        - support validation

    Does not own:
        - FastAPI construction
        - ApplicationStartup construction
        - route construction
        - submission execution
    """

    VERSION = "1.3"

    def create(
        self,
        *,
        entry=None,
        support: (
            FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport
            | None
        ) = None,
    ) -> FastAPIApplicationLifespanHTTPRuntimeIntegration:
        active_entry = entry

        if active_entry is None:
            active_entry = (
                FastAPIHTTPEntryLifespanIntegrationFactory()
                .create()
            )

        active_support = (
            support
            or FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport()
        )

        integration = (
            FastAPIApplicationLifespanHTTPRuntimeIntegration(
                entry=active_entry,
                support=active_support,
            )
        )

        if not integration.ready():
            raise RuntimeError(
                "application lifespan HTTP runtime integration unavailable"
            )

        return integration

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIApplicationLifespanHTTPRuntimeIntegrationFactory",
]
