from __future__ import annotations

from collections.abc import Callable

from backend.api.server.application_lifespan import (
    ApplicationLifespan,
)


class ApplicationLifespanFactory:
    """
    Construction boundary for the canonical application lifespan.

    Owns only:
        - ApplicationLifespan construction
        - explicit bootstrap/shutdown dependency injection
        - construction-time readiness validation

    Does not own:
        - bootstrap implementation
        - shutdown implementation
        - FastAPI application construction
        - lifespan execution
        - HTTP route construction
        - runtime execution
    """

    VERSION = "1.1"

    def create(
        self,
        *,
        bootstrap: Callable,
        shutdown: Callable,
        orchestrator=None,
    ) -> ApplicationLifespan:
        if not self.ready():
            raise RuntimeError(
                "application lifespan factory unavailable"
            )

        if not callable(bootstrap):
            raise TypeError(
                "bootstrap callable required"
            )

        if not callable(shutdown):
            raise TypeError(
                "shutdown callable required"
            )

        lifespan = ApplicationLifespan(
            bootstrap=bootstrap,
            shutdown=shutdown,
            orchestrator=orchestrator,
        )

        if not lifespan.ready():
            raise RuntimeError(
                "application lifespan unavailable"
            )

        return lifespan

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationLifespanFactory",
]
