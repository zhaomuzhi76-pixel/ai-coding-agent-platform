"""WSAgentBootstrap: WS 路由 + 连接管理注册（执行在 platform）。"""
from __future__ import annotations

from backend.api.server.ws_agent_handler_factory import (
    WSAgentHandlerFactory,
)
from backend.api.server.ws_agent_route_registration import (
    WSAgentRouteRegistration,
)
from backend.api.ws_agent import (
    register_handler,
    router as ws_router,
)
from backend.core.ws.connection_manager import ConnectionManager
from backend.core.ws.connection_registry import ConnectionRegistry
from backend.core.ws.session_id_generator import SessionIdGenerator


class WSAgentBootstrap:
    VERSION = "6.0"

    HANDLER_STATE_KEY = "ws_agent_handler"
    CONNECTION_MANAGER_STATE_KEY = "ws_agent_connection_manager"

    def __init__(
        self,
        handler_factory: WSAgentHandlerFactory | None = None,
        route_registration: WSAgentRouteRegistration | None = None,
    ) -> None:
        self.handler_factory = (
            handler_factory or WSAgentHandlerFactory()
        )
        self.route_registration = (
            route_registration or WSAgentRouteRegistration()
        )

    def build(self, startup: object, app: object) -> object:
        self._validate_application(app)
        handler = self.handler_factory.create()
        connection_manager = ConnectionManager(
            registry=ConnectionRegistry(),
            session_id_generator=SessionIdGenerator(),
        )
        if not connection_manager.ready():
            raise RuntimeError("websocket connection manager unavailable")
        register_handler(handler, connection_manager, app.state)
        self.route_registration.register(app, ws_router)
        setattr(app.state, self.HANDLER_STATE_KEY, handler)
        setattr(
            app.state,
            self.CONNECTION_MANAGER_STATE_KEY,
            connection_manager,
        )
        return handler

    async def stop(self, app: object) -> None:
        self._validate_application(app)
        manager = getattr(
            app.state, self.CONNECTION_MANAGER_STATE_KEY, None,
        )
        try:
            if manager is not None:
                close_all = getattr(manager, "close_all", None)
                if callable(close_all):
                    await close_all()
        finally:
            self.route_registration.unregister(app)
            self._clear_state(app, self.HANDLER_STATE_KEY)
            self._clear_state(
                app, self.CONNECTION_MANAGER_STATE_KEY,
            )

    def ready(self) -> bool:
        return (
            self.handler_factory is not None
            and self.handler_factory.ready()
            and self.route_registration is not None
            and self.route_registration.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_application(app: object) -> None:
        if app is None:
            raise ValueError("application required")
        if getattr(app, "state", None) is None:
            raise TypeError("application state required")

    @staticmethod
    def _clear_state(app: object, name: str) -> None:
        if hasattr(app.state, name):
            delattr(app.state, name)


__all__ = ["WSAgentBootstrap"]
