from __future__ import annotations

from typing import Protocol

from backend.workspace.project.project_model import (
    ProjectModel,
)


class ProjectPersistenceContract(Protocol):
    async def save(
        self,
        project: ProjectModel,
    ) -> None:
        ...

    async def get(
        self,
        project_id: str,
    ) -> ProjectModel | None:
        ...

    async def list(
        self,
    ) -> tuple[ProjectModel, ...]:
        ...

    async def delete(
        self,
        project_id: str,
    ) -> bool:
        ...


__all__ = [
    "ProjectPersistenceContract",
]
