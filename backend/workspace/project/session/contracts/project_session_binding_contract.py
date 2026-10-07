from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionBindingContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical project-session binding contract.

    Owns:
        - project/session identity alignment
        - workspace/session identity alignment
        - runtime/session identity alignment
        - canonical root projection

    Does not own:
        - project implementation
        - workspace implementation
        - runtime implementation
        - session persistence
        - execution lifecycle
        - agent execution
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

    def validate_alignment(self) -> None:
        ...
