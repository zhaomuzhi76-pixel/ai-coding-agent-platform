from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)


@runtime_checkable
class WorkspaceRuntimeFactoryContract(Protocol):
    """Workspace runtime construction port."""

    def create(
        self,
        root_path: str,
    ) -> WorkspaceRuntimeContract:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "WorkspaceRuntimeFactoryContract",
]
