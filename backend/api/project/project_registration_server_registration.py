from __future__ import annotations
from fastapi import FastAPI
from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_registration_api_contract import (
    ProjectRegistrationAPIContract,
)
from backend.api.project.project_registration_api_factory import (
    ProjectRegistrationAPIFactory,
)
from backend.api.project.project_registration_router import ProjectRegistrationRouter

from backend.api.project.project_workspace_server_registration import ProjectWorkspaceServerRegistration
from backend.api.project.project_registration_router_factory import ProjectRegistrationRouterFactory
from backend.api.project.project_registration_server_registration_contract import ProjectRegistrationServerRegistrationContract
from backend.api.project.project_registration_server_registration_support import ProjectRegistrationServerRegistrationSupport
from backend.application.project.project_removal_contract import ApplicationProjectRemovalContract
class ProjectRegistrationServerRegistration(
    ProjectRegistrationServerRegistrationContract,
):

    VERSION = "2.0"
    STATE_KEY = "project_registration_server"

    def __init__(
        self,
        router_factory: ProjectRegistrationRouterFactory | None = None,
        api_factory: ProjectRegistrationAPIFactory | None = None,
        support: ProjectRegistrationServerRegistrationSupport | None = None,
    ) -> None:
        self.router_factory = (
            router_factory
            or ProjectRegistrationRouterFactory()
        )
        self.api_factory = (
            api_factory
            or ProjectRegistrationAPIFactory()
        )
        self.support = (
            support
            or ProjectRegistrationServerRegistrationSupport()
        )

        self.api: ProjectRegistrationAPIContract | None = None
        self.router: ProjectRegistrationRouter | None = None
        self.workspace_registration = (
            ProjectWorkspaceServerRegistration()
        )
        self._registered_routes: tuple[object, ...] = ()

    def register(
        self,
        app: object,
        startup: object,
    ) -> object:
        app = self.support.application(app)
        self.unregister(app)

        owner = self.support.project_registration(
            startup
        )
        removal = self.support.project_removal(
            startup
        )

        if not isinstance(
            removal,
            ApplicationProjectRemovalContract,
        ):
            raise TypeError(
                "startup project removal owner invalid"
            )

        if not self.ready():
            raise RuntimeError(
                "project registration server "
                "registration unavailable"
            )

        api = self.api_factory.create(
            registration=owner,
            removal=removal,
        )

        router = self.router_factory.create(
            api
        )

        if not router.ready():
            raise RuntimeError(
                "project registration router unavailable"
            )

        before = {
            id(route)
            for route in app.router.routes
        }

        app.include_router(
            router.router
        )

        workspace_added = (
            self.workspace_registration.register(
                app,
                api,
            )
        )

        added = tuple(
            route
            for route in app.router.routes
            if id(route) not in before
        )

        if not added:
            raise RuntimeError(
                "project registration router "
                "produced no routes"
            )

        self.api = api
        self.router = router
        self._registered_routes = (
            *added,
            *workspace_added,
        )

        setattr(
            app.state,
            self.STATE_KEY,
            self,
        )

        return app

    def unregister(
        self,
        app: object,
    ) -> None:
        app = self.support.application(app)

        route_ids = {
            id(route)
            for route in self._registered_routes
        }

        if route_ids:
            app.router.routes[:] = [
                route
                for route in app.router.routes
                if id(route) not in route_ids
            ]

        current = getattr(
            app.state,
            self.STATE_KEY,
            None,
        )

        if current is self:
            delattr(
                app.state,
                self.STATE_KEY,
            )

        self._registered_routes = ()
        self.api = None
        self.router = None
        self.workspace_router = None

    def registered(
        self,
    ) -> bool:
        return bool(
            self._registered_routes
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.api_factory.ready()
            and self.router_factory.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registered": self.registered(),
            "route_count": len(
                self._registered_routes
            ),
            "api": (
                type(self.api).__name__
                if self.api is not None
                else None
            ),
            "router": (
                type(self.router).__name__
                if self.router is not None
                else None
            ),
            "workspace_registration":
                type(
                    self.workspace_registration
                ).__name__,
            "api_factory": self.api_factory.dump(),
            "router_factory": self.router_factory.dump(),
            "support": self.support.dump(),
        }


__all__ = [
    "ProjectRegistrationServerRegistration",
]
