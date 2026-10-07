from __future__ import annotations

from fastapi import FastAPI

from backend.application.project.project_registration_contract import (
    ApplicationProjectRegistrationContract,
)
from backend.application.project.project_removal_contract import (
    ApplicationProjectRemovalContract,
)


class ProjectRegistrationServerRegistrationSupport:
    """
    Validation support for project-registration server integration.

    Owns:
        - FastAPI application validation
        - startup project-registration owner resolution
        - startup project-removal owner resolution

    Does not own:
        - API construction
        - router construction
        - project construction
        - project removal construction
        - route registration
    """

    VERSION = "2.0"

    @staticmethod
    def application(
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

    @classmethod
    def project_registration(
        cls,
        startup: object,
    ) -> ApplicationProjectRegistrationContract:
        if startup is None:
            raise ValueError(
                "startup required"
            )

        state = getattr(
            startup,
            "state",
            None,
        )

        context = getattr(
            state,
            "context",
            None,
        )

        owner = (
            context.get(
                "project_registration"
            )
            if isinstance(
                context,
                dict,
            )
            else None
        )

        if owner is None:
            owner = getattr(
                startup,
                "project_registration",
                None,
            )

        if not isinstance(
            owner,
            ApplicationProjectRegistrationContract,
        ):
            raise TypeError(
                "startup project registration owner "
                "unavailable"
            )

        if not owner.ready():
            raise RuntimeError(
                "startup project registration owner "
                "not ready"
            )

        return owner

    @staticmethod
    def project_removal(
        startup: object,
    ) -> ApplicationProjectRemovalContract:
        if startup is None:
            raise ValueError(
                "startup required"
            )

        state = getattr(
            startup,
            "state",
            None,
        )

        context = getattr(
            state,
            "context",
            None,
        )

        removal = (
            context.get(
                "project_removal"
            )
            if isinstance(
                context,
                dict,
            )
            else None
        )

        if not isinstance(
            removal,
            ApplicationProjectRemovalContract,
        ):
            raise TypeError(
                "startup project removal owner "
                "unavailable"
            )

        if not removal.ready():
            raise RuntimeError(
                "startup project removal owner "
                "not ready"
            )

        return removal

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
    "ProjectRegistrationServerRegistrationSupport",
]
