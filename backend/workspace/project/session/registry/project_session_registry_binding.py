from __future__ import annotations

from backend.workspace.project.project_model import (
    ProjectModel,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.registry.project_session_registry import (
    ProjectSessionRegistry,
)


class ProjectSessionRegistryBinding:
    """
    Structural binding between project and session registries.

    Owns:
        - project existence validation
        - session/project/root alignment
        - coordinated registration and removal

    Does not own:
        - project construction
        - session construction
        - runtime lifecycle
        - workspace
        - persistence
        - execution
    """

    VERSION = "1.0"

    def __init__(
        self,
        project_registry: ProjectRegistryContract,
        session_registry: ProjectSessionRegistry,
    ) -> None:
        if not isinstance(
            project_registry,
            ProjectRegistryContract,
        ):
            raise TypeError(
                "project_registry must ProjectRegistryContract"
            )

        if not isinstance(
            session_registry,
            ProjectSessionRegistry,
        ):
            raise TypeError(
                "session_registry must ProjectSessionRegistry"
            )

        self.project_registry = project_registry
        self.session_registry = session_registry

    def register(
        self,
        session: ProjectSessionContract,
    ) -> None:
        self._validate_session(session)

        project = self._resolve_project(
            session.project_id
        )

        if project.root_path != session.root_path:
            raise ValueError(
                "session and project root mismatch"
            )

        self._validate_workspace_identity(
            project,
            session,
        )
        self.session_registry.register(
            session
        )

    def remove(
        self,
        session_id: str,
    ) -> bool:
        return self.session_registry.remove(
            session_id
        )

    def get(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.session_registry.get(
            session_id
        )

    def find_by_project(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        self._resolve_project(project_id)

        return self.session_registry.find_by_project(
            project_id
        )

    def count(
        self,
    ) -> int:
        return self.session_registry.count()

    def ready(
        self,
    ) -> bool:
        return (
            self.project_registry.ready()
            and self.session_registry.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "project_registry": (
                self.project_registry.dump()
            ),
            "session_registry": (
                self.session_registry.dump()
            ),
        }

    def _resolve_project(
        self,
        project_id: str,
    ) -> ProjectModel:
        try:
            return self.project_registry.get(
                project_id
            )
        except KeyError as error:
            raise KeyError(
                f"project not registered: {project_id}"
            ) from error

    @staticmethod
    def _validate_session(
        session: ProjectSessionContract,
    ) -> None:
        if not isinstance(
            session,
            ProjectSessionContract,
        ):
            raise TypeError(
                "session must ProjectSessionContract"
            )

    @staticmethod
    def _validate_workspace_identity(
        project: ProjectModel,
        session: ProjectSessionContract,
    ) -> None:
        project_workspace_id = (
            project.workspace_id
        )
        session_workspace_id = (
            session.workspace_id
        )

        if (
            project_workspace_id is not None
            and session_workspace_id is not None
            and project_workspace_id
            != session_workspace_id
        ):
            raise ValueError(
                "session and project workspace mismatch"
            )


__all__ = [
    "ProjectSessionRegistryBinding",
]
