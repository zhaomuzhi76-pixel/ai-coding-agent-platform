from __future__ import annotations

from fastapi import FastAPI

from backend.api.application_lifecycle.application_http_integration.fastapi_application_lifespan_http_route_observer import (
    FastAPIApplicationLifespanHTTPRouteObserver,
)


class FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport:
    """
    Validation support for the application-lifespan HTTP runtime
    integration.

    Owns:
        - application validation
        - startup validation
        - lower HTTP entry structural validation
        - registration policy projection

    Route-tree traversal is delegated to the dedicated observer.
    """

    VERSION = "1.6"

    REQUIRED_PATHS = (
        "/api/submission",
    )

    OBSERVER = (
        FastAPIApplicationLifespanHTTPRouteObserver
    )

    @staticmethod
    def validate_application(
        application: object,
    ) -> FastAPI:
        if not isinstance(
            application,
            FastAPI,
        ):
            raise TypeError(
                "application must FastAPI"
            )

        return application

    @staticmethod
    def validate_startup(
        startup: object,
    ) -> object:
        if startup is None:
            raise ValueError(
                "startup required"
            )

        return startup

    @staticmethod
    def validate_entry(
        entry: object,
    ) -> object:
        if entry is None:
            raise ValueError(
                "http entry required"
            )

        required = (
            "start",
            "stop",
            "registered",
            "ready",
            "dump",
        )

        missing = tuple(
            name
            for name in required
            if not callable(
                getattr(
                    entry,
                    name,
                    None,
                )
            )
        )

        if missing:
            raise TypeError(
                "http entry missing required methods: "
                + ", ".join(missing)
            )

        if not bool(
            entry.ready()
        ):
            raise RuntimeError(
                "http entry not ready"
            )

        return entry

    @classmethod
    def registration_valid(
        cls,
        entry,
        application,
    ) -> bool:
        if not bool(
            entry.registered()
        ):
            return False

        if not cls._requires_real_routes(
            entry
        ):
            return True

        return not cls.OBSERVER.missing_required_paths(
            application
        )

    @classmethod
    def registration_error(
        cls,
        entry,
        application,
    ) -> str:
        missing = cls.OBSERVER.missing_required_paths(
            application
        )

        if missing:
            return (
                "HTTP routes not registered: "
                + ", ".join(missing)
            )

        return (
            "http entry integration not registered"
        )

    @staticmethod
    def _requires_real_routes(
        entry,
    ) -> bool:
        return getattr(
            entry,
            "application",
            None,
        ) is not None

    @classmethod
    def route_paths(
        cls,
        application: FastAPI,
    ) -> tuple[str, ...]:
        return cls.OBSERVER.route_paths(
            application
        )

    @classmethod
    def missing_required_paths(
        cls,
        application: FastAPI,
    ) -> tuple[str, ...]:
        return cls.OBSERVER.missing_required_paths(
            application
        )

    @classmethod
    def walk_routes(
        cls,
        node,
        seen=None,
    ):
        yield from cls.OBSERVER.walk_routes(
            node,
            seen,
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
            "required_paths": self.REQUIRED_PATHS,
            "route_observer": self.OBSERVER.dump(),
        }


__all__ = [
    "FastAPIApplicationLifespanHTTPRuntimeIntegrationSupport",
]
