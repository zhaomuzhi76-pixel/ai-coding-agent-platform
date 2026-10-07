from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionRuntimeContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """Canonical project-session runtime boundary."""

    @property
    def session_id(self) -> str:
        ...

    @property
    def project_id(self) -> str:
        ...

    @property
    def root_path(self) -> str:
        ...

    def start(self) -> None:
        ...

    def close(self) -> None:
        ...

    def get_filesystem(self) -> object:
        ...

    def get_index(self) -> object:
        ...

    def get_query(self) -> object:
        ...

    def get_operations(self) -> object:
        ...


__all__ = [
    "ProjectSessionRuntimeContract",
]
