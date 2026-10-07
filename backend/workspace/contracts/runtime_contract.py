from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.workspace.contracts.workspace_contract import WorkspaceContract


@runtime_checkable
class WorkspaceRuntimeContract(
    WorkspaceContract,
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical workspace runtime contract.

    Owns:
        - active workspace runtime boundary
        - workspace capability exposure
        - runtime lifecycle closing

    Does not own:
        - filesystem implementation
        - indexing implementation
        - query implementation
        - tool execution
        - agent execution
    """

    def get_context(self) -> object:
        ...

    def get_service(self) -> object:
        ...

    def get_repository(self) -> object:
        ...

    def get_index(self) -> object:
        ...

    def get_query(self) -> object:
        ...

    def get_filesystem(self) -> object:
        ...

    def get_operations(self) -> object:
        ...

    def close(self) -> None:
        ...


__all__ = [
    "WorkspaceRuntimeContract",
]
