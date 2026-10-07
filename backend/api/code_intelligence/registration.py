from __future__ import annotations

from fastapi import FastAPI

from backend.api.code_intelligence.factory import CodeIntelligenceAPIFactory
from backend.api.code_intelligence.router import CodeIntelligenceRouter
from backend.application.capability.code_intelligence_contract import (
    CodeIntelligenceApplicationCapabilityProtocol,
)


class CodeIntelligenceServerRegistration:
    VERSION = "1.0"
    STATE_KEY = "code_intelligence_server_registration"

    def __init__(
        self,
        factory: CodeIntelligenceAPIFactory | None = None,
    ) -> None:
        self.factory = (
            factory or CodeIntelligenceAPIFactory()
        )
        self.api = None
        self.router = None
        self._routes: tuple[object, ...] = ()

    def register(
        self,
        app: FastAPI,
        startup: object,
    ) -> None:
        if not isinstance(app, FastAPI):
            raise TypeError("app must FastAPI")

        self.unregister(app)

        capability = self._resolve(startup)
        api = self.factory.create(capability)
        router = CodeIntelligenceRouter(api)

        before = {
            id(route)
            for route in app.router.routes
        }

        app.include_router(router.router)

        added = tuple(
            route
            for route in app.router.routes
            if id(route) not in before
        )

        if not added:
            raise RuntimeError(
                "code intelligence router registration produced no routes"
            )

        self.api = api
        self.router = router
        self._routes = added

        setattr(
            app.state,
            self.STATE_KEY,
            self,
        )

    def unregister(self, app: FastAPI) -> None:
        if not isinstance(app, FastAPI):
            raise TypeError("app must FastAPI")

        route_ids = {
            id(route)
            for route in self._routes
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

        self.api = None
        self.router = None
        self._routes = ()

    def registered(self) -> bool:
        return bool(
            self._routes
            and self.api is not None
            and self.router is not None
        )

    def ready(self) -> bool:
        return self.factory.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registered": self.registered(),
            "route_count": len(self._routes),
        }

    @staticmethod
    def _resolve(
        startup: object,
    ) -> CodeIntelligenceApplicationCapabilityProtocol:
        if startup is None:
            raise ValueError("startup required")

        binding = getattr(
            startup,
            "code_intelligence_binding",
            None,
        )
        capability = getattr(
            binding,
            "capability",
            None,
        )

        if not isinstance(
            capability,
            CodeIntelligenceApplicationCapabilityProtocol,
        ):
            raise TypeError(
                "startup code intelligence capability contract unavailable"
            )

        if not capability.ready():
            raise RuntimeError(
                "startup code intelligence capability not ready"
            )

        return capability


__all__ = ["CodeIntelligenceServerRegistration"]
