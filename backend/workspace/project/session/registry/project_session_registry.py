from __future__ import annotations

from backend.core.module.base_manager import BaseManager
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.contracts.project_session_registry_contract import (
    ProjectSessionRegistryContract,
)
from backend.workspace.project.session.registry.project_session_registry_support import (
    ProjectSessionRegistrySupport,
)


class ProjectSessionRegistry(
    BaseManager,
    ProjectSessionRegistryContract,
):
    """
    In-memory programming-project session registry.

    Owns:
        - session collection
        - session-id uniqueness
        - deterministic registration order
        - project/root lookup delegation

    Does not own:
        - construction
        - lifecycle implementation
        - runtime
        - workspace
        - persistence
        - execution
    """

    VERSION = "1.1"
    COMPONENT_TYPE = "project_session_registry"
    CAPABILITIES = (
        "register",
        "lookup",
        "remove",
    )

    def __init__(self) -> None:
        super().__init__(
            name="project_session_registry"
        )
        self._sessions: dict[
            str,
            ProjectSessionContract,
        ] = {}
        self._support = (
            ProjectSessionRegistrySupport()
        )

    def register(
        self,
        session: ProjectSessionContract,
    ) -> None:
        self._support.validate_session(
            session
        )

        session_id = session.session_id

        if session_id in self._sessions:
            raise ValueError(
                f"session already registered: {session_id}"
            )

        self._sessions[session_id] = session
        self.touch()

    def get(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        session_id = self._support.validate_id(
            session_id
        )

        session = self._sessions.get(
            session_id
        )

        if session is None:
            raise KeyError(
                f"session not registered: {session_id}"
            )

        return session

    def find_by_project(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        project_id = self._support.validate_id(
            project_id,
            "project id",
        )

        return tuple(
            session
            for session in self._sessions.values()
            if session.project_id == project_id
        )

    def find_by_root(
        self,
        root_path: str,
    ) -> tuple[ProjectSessionContract, ...]:
        root_path = self._support.validate_root(
            root_path
        )

        return tuple(
            session
            for session in self._sessions.values()
            if session.root_path == root_path
        )

    def remove(
        self,
        session_id: str,
    ) -> bool:
        session_id = self._support.validate_id(
            session_id
        )

        if session_id not in self._sessions:
            return False

        del self._sessions[session_id]
        self.touch()
        return True

    def contains(
        self,
        session_id: str,
    ) -> bool:
        session_id = self._support.validate_id(
            session_id
        )
        return session_id in self._sessions

    def all(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        return tuple(
            self._sessions.values()
        )

    def count(
        self,
    ) -> int:
        return len(
            self._sessions
        )

    def ready(
        self,
    ) -> bool:
        return (
            super().ready()
            and self._support.ready()
            and all(
                self._support.session_ready(
                    session
                )
                for session in self._sessions.values()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            **super().dump(),
            "registry": {
                "count": self.count(),
                "session_ids": tuple(
                    self._sessions.keys()
                ),
                "project_ids": tuple(
                    session.project_id
                    for session in self._sessions.values()
                ),
            },
            "support": self._support.dump(),
        }


__all__ = [
    "ProjectSessionRegistry",
]
