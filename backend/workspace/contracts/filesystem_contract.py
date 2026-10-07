from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class WorkspaceFilesystemContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical workspace filesystem boundary.

    Owns:
        - workspace-scoped path resolution
        - file existence
        - file reads
        - file writes

    Does not own:
        - indexing
        - search
        - analysis
        - execution
    """

    def resolve(
        self,
        path: str,
    ) -> Path:
        ...

    def exists(
        self,
        path: str,
    ) -> bool:
        ...

    def read_text(
        self,
        path: str,
    ) -> str:
        ...

    def write_text(
        self,
        path: str,
        content: str,
    ) -> None:
        ...
