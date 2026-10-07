from __future__ import annotations

from typing import Any


class ApplicationStartupAssemblySupport:
    """
    Validation support for ApplicationStartupAssembly.
    """

    VERSION = "2.0"

    @staticmethod
    def require_runtime(
        context: dict[str, Any],
    ) -> Any:
        runtime = context.get("runtime")
        if runtime is None:
            raise RuntimeError(
                "runtime construction required"
            )
        return runtime

    @staticmethod
    def require_agent_service(
        context: dict[str, Any],
    ) -> Any:
        service = context.get("agent_service")
        if service is None:
            raise RuntimeError(
                "application agent service required"
            )
        return service

    @staticmethod
    def require_project_session_service(
        composition: Any,
        project_registry: Any,
    ) -> Any:
        if project_registry is None:
            raise RuntimeError(
                "shared project registry unavailable"
            )

        service = composition.create(
            project_registry=project_registry
        ).get("session_service")

        if service is None:
            raise RuntimeError(
                "project session service unavailable"
            )

        return service

    @staticmethod
    def validate_context(
        context: dict[str, object],
    ) -> None:
        if not isinstance(context, dict):
            raise TypeError(
                "startup context must dict"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationStartupAssemblySupport",
]
