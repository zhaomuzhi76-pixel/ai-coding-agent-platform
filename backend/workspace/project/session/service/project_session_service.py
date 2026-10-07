from __future__ import annotations

from backend.core.module.base_service import BaseService
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
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)
from backend.workspace.project.session.service.project_session_service_dispatcher import (
    ProjectSessionServiceDispatcher,
)
from backend.workspace.project.session.service.project_session_service_operations import (
    ProjectSessionServiceOperations,
)
from backend.workspace.project.session.service.project_session_service_support import (
    ProjectSessionServiceSupport,
)


class ProjectSessionService(
    BaseService,
    ProjectSessionServiceContract,
):
    """
    Canonical project-session business service.

    Owns:
        - public service boundary
        - operation delegation
        - dependency readiness

    Does not own:
        - project/session construction
        - registry storage
        - lifecycle state
        - runtime/workspace construction
    """

    VERSION = "1.3"
    COMPONENT_TYPE = "project_session_service"
    CAPABILITIES = (
        "create_session",
        "get_session",
        "start_session",
        "close_session",
        "remove_session",
        "project_sessions",
        "active_sessions",
    )

    def __init__(
        self,
        project_registry: ProjectRegistryContract,
        session_registry: ProjectSessionRegistryContract,
        lifecycle: ProjectSessionLifecycleContract,
        session_factory: ProjectSessionModelFactory,
        support: ProjectSessionServiceSupport | None = None,
    ) -> None:
        super().__init__(
            name="project_session_service"
        )
        self._validate_dependencies(
            project_registry,
            session_registry,
            lifecycle,
            session_factory,
        )
        self.support = (
            support
            or ProjectSessionServiceSupport()
        )
        self.operations = ProjectSessionServiceOperations(
            project_registry=project_registry,
            session_registry=session_registry,
            lifecycle=lifecycle,
            session_factory=session_factory,
            support=self.support,
        )
        self.dispatcher = ProjectSessionServiceDispatcher(
            self.operations,
            self.support,
        )

    @staticmethod
    def _validate_dependencies(
        project_registry,
        session_registry,
        lifecycle,
        session_factory,
    ) -> None:
        if not isinstance(
            project_registry,
            ProjectRegistryContract,
        ):
            raise TypeError(
                "project_registry must "
                "ProjectRegistryContract"
            )
        if not isinstance(
            session_registry,
            ProjectSessionRegistryContract,
        ):
            raise TypeError(
                "session_registry must "
                "ProjectSessionRegistryContract"
            )
        if not isinstance(
            lifecycle,
            ProjectSessionLifecycleContract,
        ):
            raise TypeError(
                "lifecycle must "
                "ProjectSessionLifecycleContract"
            )
        if not isinstance(
            session_factory,
            ProjectSessionModelFactory,
        ):
            raise TypeError(
                "session_factory must "
                "ProjectSessionModelFactory"
            )

    def create_session(
        self,
        project_id: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectSessionContract:
        return self.operations.create_session(
            project_id,
            session_id,
            workspace_id,
            runtime_id,
            metadata,
        )

    def get_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.operations.get_session(session_id)

    def start_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.operations.start_session(session_id)

    def close_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.operations.close_session(session_id)

    def remove_session(
        self,
        session_id: str,
    ) -> bool:
        return self.operations.remove_session(session_id)

    def project_sessions(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        return self.operations.project_sessions(project_id)

    def active_sessions(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        return self.operations.active_sessions()

    def execute(
        self,
        request: dict[str, object],
    ) -> object:
        return self.dispatcher.execute(request)

    def ready(self) -> bool:
        return (
            super().ready()
            and self.operations.ready()
            and self.dispatcher.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            **super().dump(),
            "service": self.operations.dump(),
            "dispatcher": self.dispatcher.dump(),
            "support": self.support.dump(),
        }

    @property
    def create_count(self) -> int:
        return self.operations.create_count

    @property
    def start_count(self) -> int:
        return self.operations.start_count

    @property
    def close_count(self) -> int:
        return self.operations.close_count

    @property
    def remove_count(self) -> int:
        return self.operations.remove_count


__all__ = [
    "ProjectSessionService",
]
