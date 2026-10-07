from __future__ import annotations

from typing import Any

from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.project_session_descriptor import (
    ProjectSessionDescriptor,
)
from backend.workspace.project.session.project_session_state import (
    ProjectSessionState,
)


class ProjectSessionModel(
    ProjectSessionContract,
):
    """
    Canonical programming-project session model.

    Owns:
        - logical session identity
        - project/workspace/runtime binding
        - session lifecycle state

    Does not own:
        - workspace construction
        - runtime execution
        - persistence
        - registry coordination
        - agent orchestration
    """

    VERSION = "1.1"

    def __init__(
        self,
        descriptor: ProjectSessionDescriptor,
    ) -> None:
        if not isinstance(
            descriptor,
            ProjectSessionDescriptor,
        ):
            raise TypeError(
                "descriptor must "
                "ProjectSessionDescriptor"
            )

        if not descriptor.ready():
            raise ValueError(
                "project session descriptor "
                "not ready"
            )

        self.descriptor = descriptor
        self.state = (
            ProjectSessionState.CREATED
        )

    @property
    def session_id(
        self,
    ) -> str:
        return self.descriptor.session_id

    @property
    def project_id(
        self,
    ) -> str:
        return self.descriptor.project_id

    @property
    def workspace_id(
        self,
    ) -> str | None:
        return self.descriptor.workspace_id

    @property
    def runtime_id(
        self,
    ) -> str | None:
        return self.descriptor.runtime_id

    @property
    def root_path(
        self,
    ) -> str:
        return self.descriptor.root_path

    @property
    def status(
        self,
    ) -> str:
        return self.state.value

    @property
    def metadata(
        self,
    ) -> dict[str, Any]:
        return dict(
            self.descriptor.metadata
        )

    def start(
        self,
    ) -> None:
        if (
            self.state
            is ProjectSessionState.CLOSED
        ):
            raise RuntimeError(
                "closed project session "
                "cannot start"
            )

        self.state = (
            ProjectSessionState.ACTIVE
        )

    def activate(
        self,
    ) -> None:
        self.start()

    def close(
        self,
    ) -> None:
        self.state = (
            ProjectSessionState.CLOSED
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.descriptor.ready()
            and self.state.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name":
                type(self).__name__,
            "version":
                self.VERSION,
            "session_id":
                self.session_id,
            "project_id":
                self.project_id,
            "workspace_id":
                self.workspace_id,
            "runtime_id":
                self.runtime_id,
            "root_path":
                self.root_path,
            "state":
                self.state.value,
            "status":
                self.status,
            "metadata":
                self.metadata,
            "ready":
                self.ready(),
        }


__all__ = [
    "ProjectSessionModel",
]
