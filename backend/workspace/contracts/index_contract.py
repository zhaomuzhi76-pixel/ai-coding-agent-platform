from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class WorkspaceIndexContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical workspace metadata index contract.

    Owns:
        - file metadata
        - module lookup
        - extension lookup
        - indexed search

    Does not own:
        - filesystem access
        - scanning policy
        - source analysis
        - persistence
    """

    def reset(
        self,
        workspace: str,
    ) -> None:
        ...

    def add(
        self,
        metadata: dict[str, Any],
    ) -> None:
        ...

    def files(
        self,
    ) -> list[dict[str, Any]]:
        ...

    def modules(
        self,
    ) -> dict[str, list[str]]:
        ...

    def extensions(
        self,
    ) -> dict[str, list[str]]:
        ...

    def find_file(
        self,
        keyword: str,
    ) -> list[dict[str, Any]]:
        ...

    def find_module(
        self,
        keyword: str,
    ) -> dict[str, list[str]]:
        ...
