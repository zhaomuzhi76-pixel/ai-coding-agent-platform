from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.workspace.project.session.runtime.project_session_runtime_contract import (
    ProjectSessionRuntimeContract,
)


@runtime_checkable
class ProjectSessionRuntimeFactoryContract(Protocol):
    """Project-session runtime construction port."""

    def create(
        self,
        project_id: str,
        root_path: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict | None = None,
    ) -> ProjectSessionRuntimeContract:
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
    "ProjectSessionRuntimeFactoryContract",
]
