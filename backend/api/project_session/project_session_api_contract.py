from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionAPIContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical HTTP-facing project-session boundary.

    Owns:
        - transport-neutral API operations
        - request validation
        - response projection

    Does not own:
        - project/session business rules
        - registry state
        - lifecycle state
        - runtime construction
        - workspace implementation
        - persistence
    """

    def create(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        ...

    def get(
        self,
        session_id: str,
    ) -> dict[str, object]:
        ...

    def start(
        self,
        session_id: str,
    ) -> dict[str, object]:
        ...

    def close(
        self,
        session_id: str,
    ) -> dict[str, object]:
        ...

    def remove(
        self,
        session_id: str,
    ) -> dict[str, object]:
        ...

    def project_sessions(
        self,
        project_id: str,
    ) -> dict[str, object]:
        ...

    def active_sessions(
        self,
    ) -> dict[str, object]:
        ...

    def execute(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        ...
