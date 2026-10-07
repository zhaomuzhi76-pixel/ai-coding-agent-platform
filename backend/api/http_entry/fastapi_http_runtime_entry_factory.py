from __future__ import annotations

from backend.api.http_entry.fastapi_http_runtime_entry import (
    FastAPIHTTPRuntimeEntry,
)
from backend.api.http_entry.fastapi_http_runtime_entry_support import (
    FastAPIHTTPRuntimeEntrySupport,
)


class FastAPIHTTPRuntimeEntryFactory:
    """
    Construction boundary for the canonical FastAPI HTTP entry.

    Owns:
        - default lifecycle construction
        - HTTP entry construction
        - construction-time readiness validation

    Does not own:
        - application startup
        - route registration
        - submission execution
        - runtime construction
    """

    VERSION = "1.1"

    def ready(
        self,
    ) -> bool:
        return True

    def create(
        self,
        *,
        lifecycle: object | None = None,
        support: FastAPIHTTPRuntimeEntrySupport | None = None,
    ) -> FastAPIHTTPRuntimeEntry:
        from backend.api.server.submission_router_lifecycle import (
            SubmissionRouterLifecycle,
        )
        if not self.ready():
            raise RuntimeError(
                "http runtime entry factory unavailable"
            )

        effective_support = (
            support
            or FastAPIHTTPRuntimeEntrySupport()
        )

        effective_lifecycle = (
            lifecycle
            if lifecycle is not None
            else SubmissionRouterLifecycle()
        )

        entry = FastAPIHTTPRuntimeEntry(
            lifecycle=effective_lifecycle,
            support=effective_support,
        )

        if not entry.ready():
            raise RuntimeError(
                "http runtime entry unavailable"
            )

        return entry

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIHTTPRuntimeEntryFactory",
]
