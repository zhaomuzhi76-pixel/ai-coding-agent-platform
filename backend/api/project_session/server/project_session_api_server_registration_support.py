from __future__ import annotations

from fastapi import FastAPI


class ProjectSessionAPIServerRegistrationSupport:
    """
    FastAPI registration support boundary.

    Owns:
        - application validation
        - component readiness validation
        - route snapshot and removal

    Does not own:
        - project-session business logic
        - route definitions
        - application composition
    """

    VERSION = "1.1"

    def validate_app(
        self,
        app: object,
    ) -> FastAPI:
        if not isinstance(
            app,
            FastAPI,
        ):
            raise TypeError(
                "app must FastAPI"
            )

        return app

    def validate_component(
        self,
        component: object,
        name: str,
    ) -> None:
        if component is None:
            raise ValueError(
                f"{name} required"
            )

        ready = getattr(
            component,
            "ready",
            None,
        )

        if not callable(ready):
            raise TypeError(
                f"{name} must expose ready()"
            )

        if not ready():
            raise RuntimeError(
                f"{name} not ready"
            )

    def snapshot(
        self,
        app: FastAPI,
    ) -> tuple[object, ...]:
        return tuple(
            app.router.routes
        )

    def route_delta(
        self,
        before: tuple[object, ...],
        app: FastAPI,
    ) -> tuple[object, ...]:
        before_ids = {
            id(route)
            for route in before
        }

        return tuple(
            route
            for route in app.router.routes
            if id(route) not in before_ids
        )

    def remove_routes(
        self,
        app: FastAPI,
        routes: tuple[object, ...],
    ) -> None:
        if not routes:
            return

        route_ids = {
            id(route)
            for route in routes
        }

        app.router.routes[:] = [
            route
            for route in app.router.routes
            if id(route) not in route_ids
        ]

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    def ready(
        self,
    ) -> bool:
        return True


__all__ = [
    "ProjectSessionAPIServerRegistrationSupport",
]
