from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical programming-project session contract.

    Owns:
        - session identity
        - project/runtime/workspace identity references
        - session root projection
        - session lifecycle boundary
        - session metadata surface

    Does not own:
        - project construction
        - workspace construction
        - runtime construction
        - filesystem implementation
        - execution
        - persistence
        - transport
        - agent orchestration
    """

    @property
    def session_id(self) -> str:
        ...

    @property
    def project_id(self) -> str:
        ...

    @property
    def workspace_id(self) -> str | None:
        ...

    @property
    def runtime_id(self) -> str | None:
        ...

    @property
    def root_path(self) -> str:
        ...

    @property
    def status(self) -> str:
        ...

    @property
    def metadata(self) -> dict[str, object]:
        ...

    def start(self) -> None:
        ...

    def close(self) -> None:
        ...
