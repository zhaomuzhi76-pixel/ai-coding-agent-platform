from __future__ import annotations

from typing import Any

from backend.workspace.project.runtime.project_runtime_contract import (
    ProjectRuntimeContract,
)
from backend.workspace.project.session.project_session_model import (
    ProjectSessionModel,
)


class ProjectSessionRuntimeBinding:
    """
    Bind a ProjectSessionModel to a ProjectRuntime.

    Owns only structural alignment between the two lower-layer
    runtime objects.
    """

    VERSION = "1.0"

    def __init__(
        self,
        session: ProjectSessionModel,
        project_runtime: ProjectRuntimeContract,
    ) -> None:
        if not isinstance(
            session,
            ProjectSessionModel,
        ):
            raise TypeError(
                "session must ProjectSessionModel"
            )

        if not isinstance(
            project_runtime,
            ProjectRuntimeContract,
        ):
            raise TypeError(
                "project_runtime must ProjectRuntime"
            )

        self.session = session
        self.project_runtime = project_runtime
        self._validate_alignment()

    def _validate_alignment(
        self,
    ) -> None:
        if (
            self.session.project_id
            != self.project_runtime.project_id
        ):
            raise ValueError(
                "session and project runtime "
                "project mismatch"
            )

        if (
            self.session.root_path
            != self.project_runtime.root_path
        ):
            raise ValueError(
                "session and project runtime "
                "root mismatch"
            )

        session_workspace_id = (
            self.session.workspace_id
        )
        project = self.project_runtime.project
        project_workspace_id = project.workspace_id

        if (
            session_workspace_id is not None
            and project_workspace_id is not None
            and session_workspace_id
            != project_workspace_id
        ):
            raise ValueError(
                "session and project runtime "
                "workspace mismatch"
            )

    def ready(
        self,
    ) -> bool:
        return (
            self.session.descriptor.ready()
            and self.project_runtime.ready()
        )

    def get_session(
        self,
    ) -> ProjectSessionModel:
        return self.session

    def get_project_runtime(
        self,
    ) -> ProjectRuntimeContract:
        return self.project_runtime

    def get_workspace(
        self,
    ) -> Any:
        if not self.project_runtime.ready():
            raise RuntimeError(
                "project runtime not ready"
            )
        return self.project_runtime.workspace

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name":
                type(self).__name__,
            "version":
                self.VERSION,
            "ready":
                self.ready(),
            "session":
                self.session.dump(),
            "project_runtime":
                self.project_runtime.dump(),
        }


__all__ = [
    "ProjectSessionRuntimeBinding",
]
