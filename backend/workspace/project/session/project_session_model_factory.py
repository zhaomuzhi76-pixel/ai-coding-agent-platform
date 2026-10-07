from __future__ import annotations

from uuid import uuid4

from backend.workspace.project.session.project_session_descriptor import (
    ProjectSessionDescriptor,
)
from backend.workspace.project.session.project_session_model import (
    ProjectSessionModel,
)


class ProjectSessionModelFactory:
    """
    Pure project-session model construction boundary.

    Owns:
        - input normalization
        - session-id generation
        - descriptor construction
        - model construction

    Does not own:
        - project lookup
        - workspace construction
        - persistence
        - runtime execution
        - registry coordination
    """

    VERSION = "1.0"

    def create(
        self,
        project_id: str,
        root_path: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict | None = None,
    ) -> ProjectSessionModel:
        project_id = self._required(
            project_id,
            "project_id",
        )

        root_path = self._required(
            root_path,
            "root_path",
        )

        if session_id is None:
            session_id = ""

        if not isinstance(
            session_id,
            str,
        ):
            raise TypeError(
                "session_id must str or None"
            )

        session_id = session_id.strip()

        if not session_id:
            session_id = (
                f"pss_{uuid4().hex}"
            )

        workspace_id = self._optional(
            workspace_id,
            "workspace_id",
        )

        runtime_id = self._optional(
            runtime_id,
            "runtime_id",
        )

        if metadata is None:
            metadata = {}

        if not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "metadata must dict"
            )

        return ProjectSessionModel(
            ProjectSessionDescriptor(
                session_id=session_id,
                project_id=project_id,
                workspace_id=workspace_id,
                runtime_id=runtime_id,
                root_path=root_path,
                metadata=metadata,
            )
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name":
                type(self).__name__,
            "version":
                self.VERSION,
            "ready":
                self.ready(),
        }

    @staticmethod
    def _required(
        value: str,
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

    @staticmethod
    def _optional(
        value: str | None,
        name: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must str or None"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} cannot be empty"
            )

        return value


__all__ = [
    "ProjectSessionModelFactory",
]
