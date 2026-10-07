from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)


@runtime_checkable
class ProjectSessionRegistryContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical project-session registry contract.

    Owns:
        - session registration
        - session identity lookup
        - project lookup
        - removal
        - deterministic registration order

    Does not own:
        - session construction
        - session lifecycle implementation
        - project construction
        - workspace construction
        - runtime construction
        - persistence
    """

    def register(
        self,
        session: ProjectSessionContract,
    ) -> None:
        ...

    def get(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def find_by_project(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        ...

    def find_by_root(
        self,
        root_path: str,
    ) -> tuple[ProjectSessionContract, ...]:
        ...

    def remove(
        self,
        session_id: str,
    ) -> bool:
        ...

    def contains(
        self,
        session_id: str,
    ) -> bool:
        ...

    def all(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        ...

    def count(
        self,
    ) -> int:
        ...
