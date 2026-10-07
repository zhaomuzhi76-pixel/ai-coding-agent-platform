from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class WorkspaceContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical programming workspace identity contract.

    Owns:
        - workspace identity
        - canonical root
        - workspace readiness

    Does not own:
        - filesystem operations
        - indexing
        - code analysis
        - persistence
        - execution
    """

    @property
    def workspace_id(self) -> str | None:
        ...

    @property
    def root_path(self) -> str:
        ...
