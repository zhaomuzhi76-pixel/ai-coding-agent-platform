from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class WorkspaceQueryContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical workspace indexed-query contract.

    Owns:
        - indexed file listing
        - suffix filtering
        - keyword lookup

    Does not own:
        - scanning
        - filesystem access
        - index construction
        - source analysis
    """

    def list_files(
        self,
    ) -> list[str]:
        ...

    def find_by_suffix(
        self,
        suffix: str,
    ) -> list[str]:
        ...

    def find(
        self,
        keyword: str,
    ) -> list[dict[str, Any]]:
        ...
