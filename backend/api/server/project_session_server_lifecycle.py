from __future__ import annotations

from fastapi import FastAPI

from backend.api.project_session.server import (
    ProjectSessionAPIServerRegistrationFactory,
)


class ProjectSessionServerLifecycle:
    """
    Project-session API server lifecycle coordinator.

    Responsibility:
        - create the server-registration component
        - inject the startup-owned project-session graph
        - register/unregister the API router

    Does not own:
        - project-session business logic
        - project registry construction
        - application composition
        - API implementation
    """

    VERSION = "2.0"
    STATE_KEY = "project_session_api_server"

    def __init__(self) -> None:
        self.registration = None

    def register(
        self,
        app: FastAPI,
        startup: object,
    ) -> None:
        self.unregister(app)

        if startup is None:
            raise ValueError(
                "startup required"
            )

        factory = (
            ProjectSessionAPIServerRegistrationFactory()
        )

        if not factory.ready():
            raise RuntimeError(
                "project session api server "
                "registration factory unavailable"
            )

        registration = factory.create()

        if not registration.ready():
            raise RuntimeError(
                "project session api server "
                "registration unavailable"
            )

        registration.register(
            app,
            startup,
        )

        if not registration.registered():
            registration.unregister(app)
            raise RuntimeError(
                "project session api server "
                "registration produced no routes"
            )

        self.registration = registration

        setattr(
            app.state,
            self.STATE_KEY,
            registration,
        )

    def unregister(
        self,
        app: FastAPI,
    ) -> None:
        registration = self.registration

        if registration is None:
            registration = getattr(
                app.state,
                self.STATE_KEY,
                None,
            )

        if registration is not None:
            registration.unregister(app)

        state = getattr(
            app.state,
            "_state",
            {},
        )

        state.pop(
            self.STATE_KEY,
            None,
        )

        self.registration = None

    def registered(
        self,
    ) -> bool:
        return (
            self.registration is not None
            and self.registration.registered()
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
            "registered": self.registered(),
        }


__all__ = [
    "ProjectSessionServerLifecycle",
]
