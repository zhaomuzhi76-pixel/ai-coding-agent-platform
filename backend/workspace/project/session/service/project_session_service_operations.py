from __future__ import annotations

from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.contracts.project_session_registry_contract import (
    ProjectSessionRegistryContract,
)
from backend.workspace.project.session.lifecycle.project_session_lifecycle_contract import (
    ProjectSessionLifecycleContract,
)
from backend.workspace.project.session.project_session_model_factory import (
    ProjectSessionModelFactory,
)
from backend.workspace.project.session.service.project_session_service_support import (
    ProjectSessionServiceSupport,
)


class ProjectSessionServiceOperations:
    """
    Project-session business operation coordinator.

    Owns:
        - project/session use cases
        - registry coordination
        - lifecycle delegation
        - cross-entity alignment
    """

    VERSION = "1.1"

    def __init__(
        self,
        project_registry: ProjectRegistryContract,
        session_registry: ProjectSessionRegistryContract,
        lifecycle: ProjectSessionLifecycleContract,
        session_factory: ProjectSessionModelFactory,
        support: ProjectSessionServiceSupport,
    ) -> None:
        self.projects = project_registry
        self.sessions = session_registry
        self.lifecycle = lifecycle
        self.factory = session_factory
        self.support = support
        self.create_count = 0
        self.start_count = 0
        self.close_count = 0
        self.remove_count = 0

    def create_session(
        self,
        project_id: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectSessionContract:
        project = self.projects.get(
            self.support.required_id(
                project_id,
                "project id",
            )
        )
        self.support.session_id_argument(session_id)
        workspace_id = self.support.optional_id(
            workspace_id,
            "workspace_id",
        )
        runtime_id = self.support.optional_id(
            runtime_id,
            "runtime_id",
        )
        metadata = self.support.metadata(metadata)
        self.support.validate_workspace(
            project,
            workspace_id,
        )

        session = self.factory.create(
            project_id=project.project_id,
            root_path=project.root_path,
            session_id=session_id,
            workspace_id=(
                workspace_id
                if workspace_id is not None
                else project.workspace_id
            ),
            runtime_id=runtime_id,
            metadata=metadata,
        )

        self.support.validate_alignment(
            project,
            session,
        )
        self.sessions.register(session)
        self.create_count += 1
        return session

    def get_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.sessions.get(
            self.support.required_id(
                session_id,
                "session id",
            )
        )

    def start_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        result = self.lifecycle.start(
            self.support.required_id(
                session_id,
                "session id",
            )
        )
        self.start_count += 1
        return result

    def close_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        result = self.lifecycle.close(
            self.support.required_id(
                session_id,
                "session id",
            )
        )
        self.close_count += 1
        return result

    def remove_session(
        self,
        session_id: str,
    ) -> bool:
        normalized = self.support.required_id(
            session_id,
            "session id",
        )

        if not self.sessions.contains(normalized):
            return False

        session = self.sessions.get(normalized)

        if session.status == "active":
            raise RuntimeError(
                "active session cannot be removed"
            )

        removed = self.sessions.remove(normalized)

        if removed:
            self.remove_count += 1

        return removed

    def project_sessions(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        project = self.projects.get(
            self.support.required_id(
                project_id,
                "project id",
            )
        )
        sessions = self.sessions.find_by_project(
            project.project_id
        )
        for session in sessions:
            self.support.validate_alignment(
                project,
                session,
            )
        return sessions

    def active_sessions(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        return self.lifecycle.active()

    def ready(self) -> bool:
        return (
            self.projects.ready()
            and self.sessions.ready()
            and self.lifecycle.ready()
            and self.factory.ready()
            and self.support.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "create_count": self.create_count,
            "start_count": self.start_count,
            "close_count": self.close_count,
            "remove_count": self.remove_count,
        }


__all__ = [
    "ProjectSessionServiceOperations",
]
