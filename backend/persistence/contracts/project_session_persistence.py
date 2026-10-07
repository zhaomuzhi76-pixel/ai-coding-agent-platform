from __future__ import annotations

from typing import Protocol

from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)


class ProjectSessionPersistenceContract(Protocol):
    async def save(
        self,
        session: ProjectSessionContract,
    ) -> None:
        ...

    async def get(
        self,
        session_id: str,
    ) -> ProjectSessionContract | None:
        ...

    async def list(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        ...

    async def delete(
        self,
        session_id: str,
    ) -> bool:
        ...


__all__ = [
    "ProjectSessionPersistenceContract",
]
