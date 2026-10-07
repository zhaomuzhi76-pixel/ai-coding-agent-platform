from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)


@runtime_checkable
class ProjectSessionOperationalContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Application operational project-session admission contract.

    Owns:
        - registered-session resolution
        - active-session admission

    Does not own:
        - session construction
        - registry storage
        - lifecycle mutation
        - runtime execution
        - workspace construction
        - transport
    """

    def resolve(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def require_registered(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...

    def require_active(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        ...
