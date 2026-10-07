from __future__ import annotations

from backend.api.submission_api import (
    SubmissionAPIRouter,
)
from backend.api.submission_route import (
    APISubmissionRoute,
)


class SubmissionAPIRouterFactory:
    """
    Construction boundary for the canonical submission API router.

    Owns only:
        - submission-route validation
        - SubmissionAPIRouter construction
        - router readiness validation

    Does not own:
        - submission execution construction
        - runtime construction
        - application lifecycle
        - server registration
    """

    VERSION = "1.0"

    def create(
        self,
        route: APISubmissionRoute,
    ) -> SubmissionAPIRouter:
        if not self.ready():
            raise RuntimeError(
                "submission api router factory unavailable"
            )

        self._validate_route(route)

        router = SubmissionAPIRouter(
            route
        )

        if not router.ready():
            raise RuntimeError(
                "submission api router unavailable"
            )

        return router

    @staticmethod
    def _validate_route(
        route: APISubmissionRoute,
    ) -> None:
        if route is None:
            raise ValueError(
                "submission route required"
            )

        if not callable(
            getattr(
                route,
                "ready",
                None,
            )
        ):
            raise TypeError(
                "submission route must expose ready()"
            )

        if not callable(
            getattr(
                route,
                "dump",
                None,
            )
        ):
            raise TypeError(
                "submission route must expose dump()"
            )

        if not route.ready():
            raise RuntimeError(
                "submission route unavailable"
            )

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
    "SubmissionAPIRouterFactory",
]
