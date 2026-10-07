from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class WorkspaceOperationContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical workspace file-operation contract.

    Owns:
        - file reads
        - file writes
        - controlled text edits
        - existence checks

    Does not own:
        - direct OS policy
        - queue
        - execution scheduling
        - agent orchestration
        - persistence
    """

    def read_file(
        self,
        path: str,
    ) -> str:
        ...

    def write_file(
        self,
        path: str,
        content: str,
    ) -> None:
        ...

    def edit_file(
        self,
        path: str,
        old_text: str,
        new_text: str,
    ) -> dict:
        ...

    def exists(
        self,
        path: str,
    ) -> bool:
        ...
