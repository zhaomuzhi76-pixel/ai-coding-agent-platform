from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)


@runtime_checkable
class ProjectSessionLifecycleContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical project-session lifecycle control boundary.

    Owns:
        - start commands
        - close commands
        - active-session inspection

    Does not own:
        - session construction
        - registry storage
        - workspace construction
        - runtime construction
        - external storage
        - execution
        - transport
    """

    def start(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def close(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def get(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def is_active(
        self,
        session_id: str,
    ) -> bool:
        ...

    def active(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        ...


__all__ = [
    "ProjectSessionLifecycleContract",
]
