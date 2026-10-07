from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProjectModelFactoryProtocol(
    Protocol,
):
    def create(
        self,
        *,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> object:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class ApplicationProjectRegistrationContract(
    Protocol,
):
    def register(
        self,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> object:
        ...

    def get(
        self,
        project_id: str,
    ) -> object:
        ...

    def contains(
        self,
        project_id: str,
    ) -> bool:
        ...

    def remove(
        self,
        project_id: str,
    ) -> object:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ProjectModelFactoryProtocol",
    "ApplicationProjectRegistrationContract",
]
