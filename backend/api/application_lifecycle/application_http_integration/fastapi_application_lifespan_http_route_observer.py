from __future__ import annotations

from fastapi import FastAPI


class FastAPIApplicationLifespanHTTPRouteObserver:
    """
    FastAPI route-tree observation boundary.

    Owns only:
        - recursive route discovery
        - included-router traversal
        - required HTTP path observation

    Does not own:
        - route construction
        - lifecycle orchestration
        - application startup
    """

    VERSION = "1.1"

    REQUIRED_PATHS = (
        "/api/submission",
    )

    @classmethod
    def walk_routes(
        cls,
        node,
        seen=None,
    ):
        if seen is None:
            seen = set()

        marker = id(node)

        if marker in seen:
            return

        seen.add(marker)

        yielded = set()

        def emit(routes):
            if routes is None:
                return

            for route in routes:
                route_marker = id(route)

                if route_marker in yielded:
                    continue

                yielded.add(route_marker)

                yield route

                yield from cls.walk_routes(
                    route,
                    seen,
                )

        routes = getattr(
            node,
            "routes",
            None,
        )

        yield from emit(routes)

        router = getattr(
            node,
            "router",
            None,
        )

        if (
            router is not None
            and router is not node
        ):
            yield from cls.walk_routes(
                router,
                seen,
            )

        original_router = getattr(
            node,
            "original_router",
            None,
        )

        if (
            original_router is not None
            and original_router is not node
        ):
            yield from cls.walk_routes(
                original_router,
                seen,
            )

    @classmethod
    def route_paths(
        cls,
        application: FastAPI,
    ) -> tuple[str, ...]:
        paths = {
            route.path
            for route in cls.walk_routes(
                application
            )
            if getattr(
                route,
                "path",
                None,
            )
        }

        return tuple(
            sorted(paths)
        )

    @classmethod
    def missing_required_paths(
        cls,
        application: FastAPI,
    ) -> tuple[str, ...]:
        paths = set(
            cls.route_paths(
                application
            )
        )

        return tuple(
            path
            for path in cls.REQUIRED_PATHS
            if path not in paths
        )

    @classmethod
    def registered(
        cls,
        application: FastAPI,
    ) -> bool:
        return not cls.missing_required_paths(
            application
        )

    @classmethod
    def dump(
        cls,
    ) -> dict[str, object]:
        return {
            "name": cls.__name__,
            "version": cls.VERSION,
            "required_paths": cls.REQUIRED_PATHS,
        }


__all__ = [
    "FastAPIApplicationLifespanHTTPRouteObserver",
]
