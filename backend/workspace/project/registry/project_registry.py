from __future__ import annotations

from backend.core.module.base_manager import BaseManager
from backend.workspace.project.project_model import ProjectModel
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)
from backend.workspace.project.registry.project_registry_identity import (
    ProjectRegistryIdentity,
)


class ProjectRegistry(
    BaseManager,
    ProjectRegistryContract,
):
    """
    Canonical in-memory programming-project registry.

    Owns:
        - project collection
        - project-id uniqueness
        - project-root uniqueness
        - project lookup/removal

    Does not own:
        - project construction
        - workspace construction
        - runtime execution
        - persistence
        - agent orchestration
    """

    VERSION = "1.1"
    COMPONENT_TYPE = "project_registry"
    CAPABILITIES = (
        "register",
        "lookup",
        "remove",
    )

    def __init__(self) -> None:
        super().__init__(
            name="project_registry"
        )
        self._projects: dict[
            str,
            ProjectModel,
        ] = {}
        self._identity = ProjectRegistryIdentity()

    def register(
        self,
        project: ProjectModel,
    ) -> None:
        self._validate_project(project)

        project_id = project.project_id
        root = self._identity.canonical_root(
            project.root_path
        )

        if project_id in self._projects:
            raise ValueError(
                f"project already registered: {project_id}"
            )

        if self.find_by_root(root) is not None:
            raise ValueError(
                f"project root already registered: {root}"
            )

        self._projects[project_id] = project
        self.touch()

    def remove(
        self,
        project_id: str,
    ) -> ProjectModel:
        project_id = self._identity.normalize_id(
            project_id
        )
        project = self._projects.pop(
            project_id,
            None,
        )

        if project is None:
            raise KeyError(
                f"project not registered: {project_id}"
            )

        self.touch()
        return project

    def get(
        self,
        project_id: str,
    ) -> ProjectModel:
        project_id = self._identity.normalize_id(
            project_id
        )
        project = self._projects.get(
            project_id
        )

        if project is None:
            raise KeyError(
                f"project not registered: {project_id}"
            )

        return project

    def find_by_root(
        self,
        root_path: str,
    ) -> ProjectModel | None:
        root = self._identity.canonical_root(
            root_path
        )

        for project in self._projects.values():
            if (
                self._identity.canonical_root(
                    project.root_path
                )
                == root
            ):
                return project

        return None

    def projects(
        self,
    ) -> tuple[ProjectModel, ...]:
        return tuple(
            self._projects.values()
        )

    def contains(
        self,
        project_id: str,
    ) -> bool:
        project_id = self._identity.normalize_id(
            project_id
        )
        return project_id in self._projects

    def count(
        self,
    ) -> int:
        return len(
            self._projects
        )

    def ready(
        self,
    ) -> bool:
        return (
            super().ready()
            and self._identity.ready()
            and all(
                project.descriptor.ready()
                for project in self._projects.values()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            **super().dump(),
            "registry": {
                "count": self.count(),
                "project_ids": tuple(
                    self._projects.keys()
                ),
                "roots": tuple(
                    project.root_path
                    for project in self._projects.values()
                ),
            },
        }

    @staticmethod
    def _validate_project(
        project: ProjectModel,
    ) -> None:
        if not isinstance(
            project,
            ProjectModel,
        ):
            raise TypeError(
                "project must ProjectModel"
            )

        if not project.descriptor.ready():
            raise ValueError(
                "project descriptor not ready"
            )


__all__ = [
    "ProjectRegistry",
]
