from __future__ import annotations

from backend.workspace.project.project_descriptor import (
    ProjectDescriptor,
)
from backend.workspace.project.project_state import (
    ProjectState,
)


class ProjectModel:
    """
    Canonical programming-project model.

    Owns:
        - logical project identity
        - project lifecycle state

    Does not own:
        - filesystem implementation
        - workspace repository
        - workspace indexing
        - persistence
        - execution
        - agent orchestration
    """

    VERSION = "1.1"

    def __init__(
        self,
        descriptor: ProjectDescriptor,
    ) -> None:
        if not isinstance(
            descriptor,
            ProjectDescriptor,
        ):
            raise TypeError(
                "descriptor must ProjectDescriptor"
            )

        if not descriptor.ready():
            raise ValueError(
                "project descriptor not ready"
            )

        self.descriptor = descriptor
        self.state = ProjectState.CREATED

    @property
    def project_id(
        self,
    ) -> str:
        return self.descriptor.project_id

    @property
    def name(
        self,
    ) -> str:
        return self.descriptor.name

    @property
    def root_path(
        self,
    ) -> str:
        return self.descriptor.root_path

    @property
    def workspace_id(
        self,
    ) -> str | None:
        return self.descriptor.workspace_id

    def activate(
        self,
    ) -> None:
        if self.state is ProjectState.CLOSED:
            raise RuntimeError(
                "closed project cannot activate"
            )

        self.state = ProjectState.ACTIVE

    def close(
        self,
    ) -> None:
        self.state = ProjectState.CLOSED

    def ready(
        self,
    ) -> bool:
        return self.descriptor.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "project": self.descriptor.dump(),
            "state": self.state.value,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectModel",
]
