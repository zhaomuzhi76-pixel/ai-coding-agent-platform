from __future__ import annotations

from fastapi import FastAPI

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_workspace_router import (
    ProjectWorkspaceRouter,
)


class ProjectWorkspaceServerRegistration:
    """
    FastAPI registration owner for Project Workspace routes.
    """

    VERSION = "1.0"

    def register(
        self,
        app: FastAPI,
        api: ProjectRegistrationAPI,
    ) -> tuple[object, ...]:
        if not isinstance(
            app,
            FastAPI,
        ):
            raise TypeError(
                "app must FastAPI"
            )

        if not isinstance(
            api,
            ProjectRegistrationAPI,
        ):
            raise TypeError(
                "api must ProjectRegistrationAPI"
            )

        router = ProjectWorkspaceRouter(
            api,
        )

        if not router.ready():
            raise RuntimeError(
                "project workspace router unavailable"
            )

        before = {
            id(route)
            for route in app.router.routes
        }

        app.include_router(
            router.router,
        )

        return tuple(
            route
            for route in app.router.routes
            if id(route) not in before
        )


__all__ = [
    "ProjectWorkspaceServerRegistration",
]
