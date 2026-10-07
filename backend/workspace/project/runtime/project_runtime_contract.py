from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectRuntimeContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """Canonical project runtime boundary."""

    @property
    def project_id(self) -> str:
        ...

    @property
    def root_path(self) -> str:
        ...

    def get_filesystem(self) -> object:
        ...

    def get_index(self) -> object:
        ...

    def get_query(self) -> object:
        ...

    def get_operations(self) -> object:
        ...

    def start(self) -> None:
        ...

    def close(self) -> None:
        ...


__all__ = [
    "ProjectRuntimeContract",
]
