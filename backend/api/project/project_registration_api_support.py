from __future__ import annotations

from backend.application.project.project_result_contract import (
    ApplicationProjectResultContract,
)


class ProjectRegistrationAPISupport:
    """
    Project-registration API validation and projection support.

    Owns:
        - payload validation
        - identity normalization
        - application result validation

    Does not own:
        - project registry access
        - project removal policy
        - project construction
        - workspace construction
        - transport routing
    """

    VERSION = "2.0"

    @staticmethod
    def payload(
        value: object,
    ) -> dict[str, object]:
        if not isinstance(value, dict):
            raise TypeError(
                "project registration payload must dict"
            )

        if not value:
            raise ValueError(
                "project registration payload required"
            )

        return dict(value)

    @staticmethod
    def required(
        value: object,
        name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{name} must str"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} required"
            )

        return value

    @staticmethod
    def optional(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                "optional project identity must str or None"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                "optional project identity cannot be empty"
            )

        return value

    @staticmethod
    def require_project(
        project: object,
    ) -> ApplicationProjectResultContract:
        if not isinstance(
            project,
            ApplicationProjectResultContract,
        ):
            raise TypeError(
                "project registration returned invalid "
                "application project result"
            )

        if not project.ready():
            raise RuntimeError(
                "project registration returned "
                "non-ready project result"
            )

        return project

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
    "ProjectRegistrationAPISupport",
]
