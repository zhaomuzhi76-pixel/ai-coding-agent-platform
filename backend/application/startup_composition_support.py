from __future__ import annotations


class ApplicationStartupCompositionSupport:
    """Validation support for application startup composition."""

    VERSION = "1.0"

    @staticmethod
    def validate(
        dependencies: dict[str, object],
    ) -> None:
        required = (
            "registry",
            "capability_composition",
            "project_session_composition",
            "project_session_operational",
            "project_registry",
            "project_registration_factory",
            "project_registration",
            "assembly",
            "state",
            "accessors",
            "planning_binding",
            "code_intelligence_binding",
            "tool_binding",
            "project_session_binding",
        )

        missing = tuple(
            key
            for key in required
            if dependencies.get(key) is None
        )

        if missing:
            raise RuntimeError(
                "application startup dependencies missing: "
                + ", ".join(missing)
            )

        project_registry = dependencies[
            "project_registry"
        ]

        ready = getattr(
            project_registry,
            "ready",
            None,
        )

        if not callable(ready):
            raise TypeError(
                "project registry must expose ready()"
            )

        if not ready():
            raise RuntimeError(
                "project registry unavailable"
            )

        project_registration = dependencies[
            "project_registration"
        ]

        if not project_registration.ready():
            raise RuntimeError(
                "project registration unavailable"
            )

        assembly = dependencies["assembly"]

        if not assembly.ready():
            raise RuntimeError(
                "application startup assembly unavailable"
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
        }


__all__ = [
    "ApplicationStartupCompositionSupport",
]
