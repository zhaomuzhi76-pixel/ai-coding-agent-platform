from __future__ import annotations

from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.contracts.project_session_registry_contract import (
    ProjectSessionRegistryContract,
)
from backend.workspace.project.session.lifecycle.project_session_lifecycle_contract import (
    ProjectSessionLifecycleContract,
)


class ProjectSessionLifecycle(
    ProjectSessionLifecycleContract,
):
    """
    Coordinates lifecycle commands for registered sessions.

    Owns:
        - lifecycle command validation
        - delegation to registered session entities
        - lifecycle operation counters

    Does not own:
        - lifecycle state storage
        - session construction
        - registry storage
        - workspace
        - runtime
        - external storage
        - execution
        - transport
    """

    VERSION = "1.2"

    def __init__(
        self,
        registry: ProjectSessionRegistryContract,
    ) -> None:
        if not isinstance(
            registry,
            ProjectSessionRegistryContract,
        ):
            raise TypeError(
                "registry must "
                "ProjectSessionRegistryContract"
            )

        self.registry = registry
        self.start_count = 0
        self.close_count = 0

    def start(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        session = self.get(
            session_id
        )

        if session.status == "closed":
            raise RuntimeError(
                "closed project session cannot start"
            )

        if session.status != "active":
            session.start()
            self.start_count += 1

        return session

    def close(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        session = self.get(
            session_id
        )

        if session.status != "closed":
            session.close()
            self.close_count += 1

        return session

    def get(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        normalized = self._normalize_id(
            session_id
        )

        return self.registry.get(
            normalized
        )

    def is_active(
        self,
        session_id: str,
    ) -> bool:
        return (
            self.get(
                session_id
            ).status
            == "active"
        )

    def active(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        return tuple(
            session
            for session in self.registry.all()
            if session.status == "active"
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.registry is not None
            and self.registry.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registered_sessions": (
                self.registry.count()
            ),
            "active_sessions": len(
                self.active()
            ),
            "start_count": self.start_count,
            "close_count": self.close_count,
        }

    @staticmethod
    def _normalize_id(
        session_id: str,
    ) -> str:
        if not isinstance(
            session_id,
            str,
        ):
            raise TypeError(
                "session id must str"
            )

        normalized = session_id.strip()

        if not normalized:
            raise ValueError(
                "session id required"
            )

        return normalized


__all__ = [
    "ProjectSessionLifecycle",
]
