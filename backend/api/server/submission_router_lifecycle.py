from __future__ import annotations

from fastapi import FastAPI

from backend.api.server.submission_router_lifecycle_support import (
    SubmissionRouterLifecycleSupport,
)
from backend.api.submission_api_router_factory import (
    SubmissionAPIRouterFactory,
)
from backend.api.submission_route import APISubmissionRoute


class SubmissionRouterLifecycle:
    """
    Submission API router lifecycle boundary.

    Owns:
        - submission route construction
        - FastAPI router registration
        - registration cleanup

    Does not own:
        - runtime-submission resolution policy
        - runtime construction
        - execution implementation
    """

    VERSION = "1.5"
    STATE_KEY = "submission_router_lifecycle"
    ROUTES_KEY = "_runtime_submission_dynamic_routers"

    def __init__(
        self,
        support: SubmissionRouterLifecycleSupport | None = None,
    ) -> None:
        self.support = (
            support
            or SubmissionRouterLifecycleSupport()
        )
        self.submission_route = None
        self.submission_router = None
        self._routes: tuple[object, ...] = ()
        self.router_factory = SubmissionAPIRouterFactory()

    def register(
        self,
        app: FastAPI,
        startup: object,
    ) -> None:
        self.support.validate_startup(startup)
        self.unregister(app)

        runtime_submission = (
            self.support.resolve_runtime_submission(startup)
        )

        submission_route = APISubmissionRoute(
            runtime_submission
        )
        if not submission_route.ready():
            raise RuntimeError(
                "submission route unavailable"
            )

        submission_router = self.router_factory.create(
            submission_route
        )

        before = {
            id(route)
            for route in app.router.routes
        }

        app.include_router(
            submission_router.router
        )

        added = tuple(
            route
            for route in app.router.routes
            if id(route) not in before
        )

        if not added:
            raise RuntimeError(
                "submission router registration produced no routes"
            )

        if (
            submission_route.binding.runtime_submission
            is not runtime_submission
        ):
            raise RuntimeError(
                "runtime submission binding identity mismatch"
            )

        self.submission_route = submission_route
        self.submission_router = submission_router
        self._routes = added

        setattr(
            app.state,
            self.STATE_KEY,
            self,
        )
        setattr(
            app.state,
            self.ROUTES_KEY,
            added,
        )

    def unregister(
        self,
        app: FastAPI,
    ) -> None:
        if self._routes:
            route_ids = {
                id(route)
                for route in self._routes
            }
            app.router.routes[:] = [
                route
                for route in app.router.routes
                if id(route) not in route_ids
            ]

        if getattr(
            app.state,
            self.STATE_KEY,
            None,
        ) is self:
            delattr(
                app.state,
                self.STATE_KEY,
            )

        if hasattr(
            app.state,
            self.ROUTES_KEY,
        ):
            delattr(
                app.state,
                self.ROUTES_KEY,
            )

        self._routes = ()
        self.submission_route = None
        self.submission_router = None

    def registered(self) -> bool:
        return bool(self._routes)

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.router_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registered": self.registered(),
            "route_count": len(self._routes),
            "submission_route": (
                self.submission_route.dump()
                if self.submission_route is not None
                else None
            ),
            "router_factory": self.router_factory.dump(),
            "support": self.support.dump(),
        }


__all__ = [
    "SubmissionRouterLifecycle",
]
