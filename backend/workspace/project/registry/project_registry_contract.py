from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.workspace.project.project_model import (
    ProjectModel,
)


@runtime_checkable
class ProjectRegistryContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical programming-project registry contract.

    Owns:
        - project registration
        - project uniqueness
        - project lookup
        - project removal

    Does not own:
        - project construction
        - workspace construction
        - runtime execution
        - persistence
        - agent orchestration
    """

    def register(
        self,
        project: ProjectModel,
    ) -> None:
        ...

    def remove(
        self,
        project_id: str,
    ) -> ProjectModel:
        ...

    def get(
        self,
        project_id: str,
    ) -> ProjectModel:
        ...

    def find_by_root(
        self,
        root_path: str,
    ) -> ProjectModel | None:
        ...

    def projects(
        self,
    ) -> tuple[ProjectModel, ...]:
        ...

    def contains(
        self,
        project_id: str,
    ) -> bool:
        ...

    def count(
        self,
    ) -> int:
        ...


__all__ = [
    "ProjectRegistryContract",
]
