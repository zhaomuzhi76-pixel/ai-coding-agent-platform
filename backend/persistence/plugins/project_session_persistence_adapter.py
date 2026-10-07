from __future__ import annotations

from backend.persistence.contracts.project_session_persistence import (
    ProjectSessionPersistenceContract,
)
from backend.persistence.plugins.persistence_sync_bridge import (
    PersistenceSyncBridge,
)
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)


class ProjectSessionPersistenceAdapter(
    ProjectSessionServiceContract,
):
    VERSION = "1.0"

    def __init__(
        self,
        service: ProjectSessionServiceContract,
        persistence: ProjectSessionPersistenceContract,
        bridge: PersistenceSyncBridge | None = None,
    ) -> None:
        if not isinstance(
            service,
            ProjectSessionServiceContract,
        ):
            raise TypeError(
                "project session service contract required"
            )

        if not persistence.ready():
            raise RuntimeError(
                "project session persistence not ready"
            )

        self.service = service
        self.persistence = persistence
        self.bridge = (
            bridge or PersistenceSyncBridge()
        )

    def create_session(
        self,
        project_id: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectSessionContract:
        session = self.service.create_session(
            project_id,
            session_id,
            workspace_id,
            runtime_id,
            metadata,
        )

        try:
            self.bridge.run(
                self.persistence.save(session)
            )
        except Exception:
            self.service.remove_session(
                session.session_id
            )
            raise

        return session

    def get_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.service.get_session(
            session_id
        )

    def start_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        session = self.service.get_session(
            session_id
        )
        previous = session.status

        result = self.service.start_session(
            session_id
        )

        try:
            self.bridge.run(
                self.persistence.save(result)
            )
        except Exception:
            if previous == "created":
                result.state = type(
                    result.state
                ).CREATED
            raise

        return result

    def close_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        session = self.service.get_session(
            session_id
        )
        previous = session.status

        result = self.service.close_session(
            session_id
        )

        try:
            self.bridge.run(
                self.persistence.save(result)
            )
        except Exception:
            if previous == "active":
                result.state = type(
                    result.state
                ).ACTIVE
            raise

        return result

    def remove_session(
        self,
        session_id: str,
    ) -> bool:
        session = self.service.get_session(
            session_id
        )

        removed = self.service.remove_session(
            session_id
        )

        if not removed:
            return False

        try:
            deleted = self.bridge.run(
                self.persistence.delete(
                    session_id
                )
            )
            if not deleted:
                raise RuntimeError(
                    "project session persistence delete failed"
                )
        except Exception:
            self.service.create_session(
                project_id=session.project_id,
                session_id=session.session_id,
                workspace_id=session.workspace_id,
                runtime_id=session.runtime_id,
                metadata=session.metadata,
            )
            raise

        return True

    def project_sessions(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        return self.service.project_sessions(
            project_id
        )

    def active_sessions(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        return self.service.active_sessions()

    def execute(
        self,
        request: dict[str, object],
    ) -> object:
        return self.service.execute(request)

    def ready(self) -> bool:
        return (
            self.service.ready()
            and self.persistence.ready()
            and self.bridge.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "service": type(
                self.service
            ).__name__,
            "persistence": type(
                self.persistence
            ).__name__,
        }


__all__ = [
    "ProjectSessionPersistenceAdapter",
]
