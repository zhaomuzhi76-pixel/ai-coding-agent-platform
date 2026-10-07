from __future__ import annotations

from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)


class ProjectSessionRegistrySupport:
    """
    Internal support for project-session registry invariants.

    Owns:
        - session identity validation
        - session structural validation
        - readiness checks

    Does not own:
        - session storage
        - project lookup
        - registration
        - removal
        - lifecycle
        - runtime
        - persistence
    """

    VERSION = "1.0"

    def validate_session(
        self,
        session: ProjectSessionContract,
    ) -> None:
        if not isinstance(
            session,
            ProjectSessionContract,
        ):
            raise TypeError(
                "session must ProjectSessionContract"
            )

        self.validate_id(
            session.session_id,
            "session id",
        )
        self.validate_id(
            session.project_id,
            "project id",
        )
        self.validate_root(
            session.root_path
        )

    def validate_id(
        self,
        value: str,
        name: str = "id",
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

    def validate_root(
        self,
        value: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "root_path must str"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                "root_path required"
            )

        return value

    def session_ready(
        self,
        session: ProjectSessionContract,
    ) -> bool:
        return (
            isinstance(
                session,
                ProjectSessionContract,
            )
            and bool(session.session_id)
            and bool(session.project_id)
            and bool(session.root_path)
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
    "ProjectSessionRegistrySupport",
]
