from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.composition.runtime_port import (
    ApplicationRuntimePortProtocol,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)


@runtime_checkable
class ApplicationRuntimeConstructionProtocol(
    Protocol,
):
    """
    Application-facing Runtime construction port.

    Concrete Runtime and Workspace implementations remain
    outside Application. Application receives only contracts.
    """

    @property
    def workspace_factory(
        self,
    ) -> WorkspaceRuntimeFactoryContract:
        ...

    def create(
        self,
    ) -> ApplicationRuntimePortProtocol:
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
    "ApplicationRuntimeConstructionProtocol",
]
