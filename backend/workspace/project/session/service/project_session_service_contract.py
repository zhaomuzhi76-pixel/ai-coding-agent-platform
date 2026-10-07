from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)


@runtime_checkable
class ProjectSessionServiceContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical project-session business service contract.

    Owns:
        - project-session business operations
        - project ownership validation
        - delegation to frozen lifecycle and registries

    Does not own:
        - project construction
        - workspace construction
        - runtime construction
        - persistence
        - transport
        - Agent orchestration
    """

    def execute(
        self,
        request: dict[str, object],
    ) -> object:
        ...

    def create_session(
        self,
        project_id: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectSessionContract:
        ...

    def get_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def start_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def close_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def remove_session(
        self,
        session_id: str,
    ) -> bool:
        ...

    def project_sessions(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        ...

    def active_sessions(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        ...
