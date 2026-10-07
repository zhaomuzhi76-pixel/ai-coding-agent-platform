from __future__ import annotations

from typing import Any

from backend.workspace.project.project_model import (
    ProjectModel,
)
from backend.workspace.project.runtime.project_runtime_binding import (
    ProjectRuntimeBinding,
)
from backend.workspace.project.runtime.project_runtime_contract import (
    ProjectRuntimeContract,
)
from backend.workspace.project.runtime.project_runtime_state import (
    ProjectRuntimeState,
)


class ProjectRuntime(ProjectRuntimeContract):
    """
    Active programming-project runtime boundary.

    Owns:
        - project runtime lifecycle state
        - access projection to frozen workspace capability contracts

    Does not own:
        - filesystem implementation
        - indexing
        - scanning
        - persistence
        - execution
        - agent orchestration
    """

    VERSION = "1.1"

    def __init__(
        self,
        binding: ProjectRuntimeBinding,
    ) -> None:
        if not isinstance(
            binding,
            ProjectRuntimeBinding,
        ):
            raise TypeError(
                "binding must ProjectRuntimeBinding"
            )

        self.binding = binding
        self.state = (
            ProjectRuntimeState.CREATED
        )

    @property
    def project(self) -> ProjectModel:
        return self.binding.project

    @property
    def workspace(self) -> Any:
        return self.binding.workspace

    @property
    def project_id(self) -> str:
        return self.project.project_id

    @property
    def root_path(self) -> str:
        return self.project.root_path

    def start(self) -> None:
        if (
            self.state
            is ProjectRuntimeState.CLOSED
        ):
            raise RuntimeError(
                "closed project runtime cannot start"
            )

        if not self.project.ready():
            self.project.activate()

        if not self.workspace.ready():
            raise RuntimeError(
                "workspace runtime not ready"
            )

        self.state = ProjectRuntimeState.ACTIVE

    def close(self) -> None:
        if (
            self.state
            is ProjectRuntimeState.CLOSED
        ):
            return

        self.workspace.close()
        self.project.close()
        self.state = ProjectRuntimeState.CLOSED

    def get_filesystem(self) -> Any:
        self._require_ready()
        return self.workspace.get_filesystem()

    def get_index(self) -> Any:
        self._require_ready()
        return self.workspace.get_index()

    def get_query(self) -> Any:
        self._require_ready()
        return self.workspace.get_query()

    def get_operations(self) -> Any:
        self._require_ready()
        return self.workspace.get_operations()

    def _require_ready(self) -> None:
        if not self.ready():
            raise RuntimeError(
                "project runtime not ready"
            )

    def ready(self) -> bool:
        return (
            self.binding.ready()
            and self.state.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "project_id": self.project_id,
            "root_path": self.root_path,
            "state": self.state.value,
            "ready": self.ready(),
            "binding": self.binding.dump(),
        }


__all__ = [
    "ProjectRuntime",
]
