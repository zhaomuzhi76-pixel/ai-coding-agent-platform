from __future__ import annotations


class WSAgentRouteRegistration:
    """
    Canonical WebSocket route registration boundary.

    Owns:
        - /ws/agent endpoint discovery
        - native FastAPI websocket registration
        - duplicate registration prevention
        - owned route cleanup
    """

    VERSION = "2.1"
    PATH = "/ws/agent"

    def __init__(self) -> None:
        self._routes: tuple[object, ...] = ()

    def register(self, app: object, router: object) -> None:
        self._validate_application(app)
        if self._registered(app):
            return

        endpoint = self._find_endpoint(router)
        add_route = getattr(app, "add_api_websocket_route", None)
        if not callable(add_route):
            raise TypeError(
                "application must expose add_api_websocket_route()"
            )

        routes = getattr(app.router, "routes", ()) or ()
        before = {id(route) for route in routes}
        add_route(
            self.PATH,
            endpoint,
            name=getattr(endpoint, "__name__", "ws_agent"),
        )

        self._routes = tuple(
            route
            for route in (getattr(app.router, "routes", ()) or ())
            if id(route) not in before
            and getattr(route, "path", None) == self.PATH
        )

        if not self._routes:
            raise RuntimeError("websocket route registration failed")

    def unregister(self, app: object) -> None:
        self._validate_application(app)
        route_ids = {id(route) for route in self._routes}
        if route_ids:
            app.router.routes[:] = [
                route
                for route in app.router.routes
                if id(route) not in route_ids
            ]
        self._routes = ()

    def registered(self, app: object) -> bool:
        return app is not None and self._registered(app)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "path": self.PATH,
            "route_count": len(self._routes),
            "ready": self.ready(),
        }

    @classmethod
    def _registered(cls, app: object) -> bool:
        return any(
            getattr(route, "path", None) == cls.PATH
            for route in (
                getattr(getattr(app, "router", None), "routes", ())
                or ()
            )
        )

    @classmethod
    def _find_endpoint(cls, router: object):
        if router is None:
            raise ValueError("websocket router required")

        endpoint = cls._walk_endpoint(router, set())
        if endpoint is None:
            raise RuntimeError("websocket route endpoint not found")
        return endpoint

    @classmethod
    def _walk_endpoint(cls, node: object, visited: set[int]):
        identity = id(node)
        if identity in visited:
            return None
        visited.add(identity)

        for route in (getattr(node, "routes", ()) or ()):
            if getattr(route, "path", None) == cls.PATH:
                endpoint = getattr(route, "endpoint", None)
                if callable(endpoint):
                    return endpoint

            endpoint = cls._walk_endpoint(route, visited)
            if endpoint is not None:
                return endpoint

            original = getattr(route, "original_router", None)
            if original is not None:
                endpoint = cls._walk_endpoint(original, visited)
                if endpoint is not None:
                    return endpoint

        return None

    @staticmethod
    def _validate_application(app: object) -> None:
        if app is None:
            raise ValueError("application required")

        router = getattr(app, "router", None)
        if router is None or not hasattr(router, "routes"):
            raise TypeError("application router required")


__all__ = ["WSAgentRouteRegistration"]
