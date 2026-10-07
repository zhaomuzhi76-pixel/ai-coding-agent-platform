from __future__ import annotations

from backend.api.application_lifecycle.http_entry_integration.fastapi_http_entry_lifespan_integration import (
    FastAPIHTTPEntryLifespanIntegration,
)
from backend.api.application_lifecycle.http_entry_integration.fastapi_http_entry_lifespan_integration_support import (
    FastAPIHTTPEntryLifespanIntegrationSupport,
)
from backend.api.http_entry.fastapi_http_runtime_entry_factory import (
    FastAPIHTTPRuntimeEntryFactory,
)


class FastAPIHTTPEntryLifespanIntegrationFactory:
    """
    Construction boundary for the FastAPI HTTP/lifespan bridge.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        entry=None,
        support: FastAPIHTTPEntryLifespanIntegrationSupport
        | None = None,
    ) -> FastAPIHTTPEntryLifespanIntegration:
        if entry is None:
            entry = FastAPIHTTPRuntimeEntryFactory().create()

        integration = (
            FastAPIHTTPEntryLifespanIntegration(
                entry=entry,
                support=support,
            )
        )

        if not integration.ready():
            raise RuntimeError(
                "HTTP lifespan integration unavailable"
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
    "FastAPIHTTPEntryLifespanIntegrationFactory",
]
