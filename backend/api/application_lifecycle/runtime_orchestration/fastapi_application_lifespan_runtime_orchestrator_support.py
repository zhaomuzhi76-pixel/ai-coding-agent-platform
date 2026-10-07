from __future__ import annotations

import inspect

from fastapi import FastAPI


class FastAPIApplicationLifespanRuntimeOrchestratorSupport:
    """
    Structural validation support for ApplicationLifespan orchestration.

    Concrete dependency inheritance is intentionally not required.
    Structural doubles remain valid test/runtime dependencies.
    """

    VERSION = "1.3"

    @staticmethod
    def validate_application(
        application: object,
    ) -> FastAPI:
        if not isinstance(application, FastAPI):
            raise TypeError("application must FastAPI")
        return application

    @staticmethod
    def validate_startup(
        startup: object,
    ) -> object:
        if startup is None:
            raise ValueError("startup required")

        required = (
            "runtime",
            "runtime_submission",
        )
        missing = tuple(
            name
            for name in required
            if getattr(startup, name, None) is None
        )

        if missing:
            raise RuntimeError(
                "startup missing required attributes: "
                + ", ".join(missing)
            )

        return startup

    @staticmethod
    def validate_http_integration(
        integration: object,
    ) -> object:
        return FastAPIApplicationLifespanRuntimeOrchestratorSupport._validate_behavior(
            integration,
            ("start", "stop", "registered", "ready", "dump"),
            "http integration",
        )

    @staticmethod
    def validate_ws_bootstrap(
        bootstrap: object,
    ) -> object:
        return FastAPIApplicationLifespanRuntimeOrchestratorSupport._validate_behavior(
            bootstrap,
            ("build", "ready", "dump"),
            "ws bootstrap",
        )

    @staticmethod
    def validate_project_session_lifecycle(
        lifecycle: object,
    ) -> object:
        return FastAPIApplicationLifespanRuntimeOrchestratorSupport._validate_behavior(
            lifecycle,
            (
                "register",
                "unregister",
                "registered",
                "ready",
                "dump",
            ),
            "project session lifecycle",
        )

    @staticmethod
    def validate_project_registration_lifecycle(
        lifecycle: object,
    ) -> object:
        return FastAPIApplicationLifespanRuntimeOrchestratorSupport._validate_behavior(
            lifecycle,
            (
                "register",
                "unregister",
                "registered",
                "ready",
                "dump",
            ),
            "project registration lifecycle",
        )

    @staticmethod
    def validate_api_lifecycle(
        lifecycle: object,
        label: str,
    ) -> object:
        return (
            FastAPIApplicationLifespanRuntimeOrchestratorSupport
            ._validate_behavior(
                lifecycle,
                (
                    "register",
                    "unregister",
                    "registered",
                    "ready",
                    "dump",
                ),
                label,
            )
        )

    @staticmethod
    def _validate_behavior(
        dependency: object,
        methods: tuple[str, ...],
        label: str,
    ) -> object:
        if dependency is None:
            raise ValueError(f"{label} required")

        missing = tuple(
            name
            for name in methods
            if not callable(
                getattr(dependency, name, None)
            )
        )

        if missing:
            raise TypeError(
                f"{label} missing required methods: "
                + ", ".join(missing)
            )

        if not bool(dependency.ready()):
            raise RuntimeError(f"{label} not ready")

        return dependency

    @staticmethod
    async def await_if_needed(
        result: object,
    ) -> None:
        if inspect.isawaitable(result):
            await result

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIApplicationLifespanRuntimeOrchestratorSupport",
]
