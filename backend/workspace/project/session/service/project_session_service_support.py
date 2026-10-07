from __future__ import annotations


class ProjectSessionServiceSupport:
    """
    Stateless service validation and normalization support.

    Owns:
        - identifier normalization
        - optional identifier validation
        - metadata validation
        - operation normalization
        - project/session alignment validation
    """

    VERSION = "1.2"

    @staticmethod
    def required_id(
        value: object,
        label: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{label} must str")
        value = value.strip()
        if not value:
            raise ValueError(f"{label} required")
        return value

    @staticmethod
    def optional_id(
        value: object,
        label: str,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{label} must str or None")
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty")
        return value

    @staticmethod
    def session_id_argument(
        value: object,
    ) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise TypeError("session id must str or None")
        if not value.strip():
            raise ValueError("session id cannot be empty")

    @staticmethod
    def metadata(
        value: object,
    ) -> dict[str, object] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError("metadata must dict")
        return dict(value)

    @staticmethod
    def operation(
        value: object,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError("operation must str")
        value = value.strip()
        if not value:
            raise ValueError("operation required")
        return value

    @staticmethod
    def validate_alignment(
        project,
        session,
    ) -> None:
        if session.project_id != project.project_id:
            raise RuntimeError(
                "session project identity mismatch"
            )
        if session.root_path != project.root_path:
            raise RuntimeError("session root mismatch")
        if (
            project.workspace_id is not None
            and session.workspace_id != project.workspace_id
        ):
            raise RuntimeError(
                "session workspace identity mismatch"
            )

    @staticmethod
    def validate_workspace(
        project,
        workspace_id: str | None,
    ) -> None:
        if (
            workspace_id is not None
            and project.workspace_id is not None
            and workspace_id != project.workspace_id
        ):
            raise ValueError(
                "session workspace identity "
                "does not match project"
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
    "ProjectSessionServiceSupport",
]
