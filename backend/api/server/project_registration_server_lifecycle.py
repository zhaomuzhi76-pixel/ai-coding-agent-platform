from __future__ import annotations

from fastapi import FastAPI

from backend.api.project.project_registration_server_registration import (
    ProjectRegistrationServerRegistration,
)
from backend.api.project.project_registration_server_registration_factory import (
    ProjectRegistrationServerRegistrationFactory,
)


class ProjectRegistrationServerLifecycle:
    """
    FastAPI project-registration server lifecycle coordinator.

    Owns:
        - server-registration factory resolution
        - startup registration
        - shutdown unregistration

    Does not own:
        - registration construction
        - project registry construction
        - project business logic
        - application startup state
        - route implementation
    """

    VERSION = "1.1"
    STATE_KEY = "project_registration_server"

    def __init__(
        self,
        factory: ProjectRegistrationServerRegistrationFactory | None = None,
    ) -> None:
        self.factory = (
            factory
            or ProjectRegistrationServerRegistrationFactory()
        )
        self.registration: (
            ProjectRegistrationServerRegistration | None
        ) = None

    def register(
        self,
        app: FastAPI,
        startup: object,
    ) -> None:
        self.unregister(app)

        if startup is None:
            raise ValueError("startup required")

        if not self.factory.ready():
            raise RuntimeError(
                "project registration server "
                "registration factory unavailable"
            )

        registration = self.factory.create()

        registration.register(
            app,
            startup,
        )

        if not registration.registered():
            registration.unregister(app)
            raise RuntimeError(
                "project registration server "
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

    def registered(self) -> bool:
        return (
            self.registration is not None
            and self.registration.registered()
        )

    def ready(self) -> bool:
        return self.factory.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registered": self.registered(),
            "factory": self.factory.dump(),
        }


__all__ = [
    "ProjectRegistrationServerLifecycle",
]
