from __future__ import annotations

from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)
from backend.workspace.project.project_model import (
    ProjectModel,
)


class ProjectRuntimeBinding:
    """
    Project-to-workspace dependency binding.

    Responsibility:
        - bind ProjectModel to the frozen workspace contract
        - validate project/workspace identity alignment
        - expose structural binding readiness

    Does not own:
        - project lifecycle activation
        - workspace construction
        - workspace implementations
        - indexing
        - filesystem
        - execution
        - persistence
    """

    VERSION = "1.2"

    def __init__(
        self,
        project: ProjectModel,
        workspace: WorkspaceRuntimeContract,
    ) -> None:
        if not isinstance(
            project,
            ProjectModel,
        ):
            raise TypeError(
                "project must ProjectModel"
            )

        if not isinstance(
            workspace,
            WorkspaceRuntimeContract,
        ):
            raise TypeError(
                "workspace must WorkspaceRuntimeContract"
            )

        self.project = project
        self.workspace = workspace
        self._validate_alignment()

    def _validate_alignment(
        self,
    ) -> None:
        if (
            self.project.root_path
            != self.workspace.root_path
        ):
            raise ValueError(
                "project and workspace root mismatch"
            )

        project_workspace_id = (
            self.project.workspace_id
        )
        workspace_id = self.workspace.workspace_id

        if (
            project_workspace_id is not None
            and workspace_id is not None
            and project_workspace_id
            != workspace_id
        ):
            raise ValueError(
                "project and workspace identity mismatch"
            )

    def ready(
        self,
    ) -> bool:
        """
        Binding readiness means dependency structure is valid.

        Project lifecycle activation belongs to ProjectRuntime.start().
        Therefore ProjectModel.ready() must not be required here.
        """
        return (
            self.project is not None
            and self.project.descriptor.ready()
            and self.workspace is not None
            and self.workspace.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "project": self.project.dump(),
            "workspace": self.workspace.dump(),
        }


__all__ = [
    "ProjectRuntimeBinding",
]
