from __future__ import annotations

from backend.api.project_session.project_session_api_result import (
    ProjectSessionAPIResult,
)


class ProjectSessionAPISupport:
    """
    API boundary validation support.

    Owns:
        - request validation
        - identity normalization
        - metadata validation
        - result support coordination

    Does not own:
        - project/session business logic
        - lifecycle
        - registry
        - transport routing
    """

    VERSION = "1.1"

    def __init__(
        self,
        result: ProjectSessionAPIResult | None = None,
    ) -> None:
        self.result = (
            result
            or ProjectSessionAPIResult()
        )

    def payload(
        self,
        value: object,
    ) -> dict[str, object]:
        if not isinstance(
            value,
            dict,
        ):
            raise TypeError(
                "project session payload must dict"
            )

        if not value:
            raise ValueError(
                "project session payload required"
            )

        return dict(value)

    def required(
        self,
        value: object,
        name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must str"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} required"
            )

        return value

    def optional(
        self,
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "optional identity must str or None"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                "optional identity cannot be empty"
            )

        return value

    def metadata(
        self,
        value: object,
    ) -> dict[str, object] | None:
        if value is None:
            return None

        if not isinstance(
            value,
            dict,
        ):
            raise TypeError(
                "metadata must dict"
            )

        return dict(value)

    def session_id(
        self,
        value: str,
    ) -> str:
        return self.required(
            value,
            "session id",
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.result.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "result": self.result.dump(),
        }


__all__ = [
    "ProjectSessionAPISupport",
]
