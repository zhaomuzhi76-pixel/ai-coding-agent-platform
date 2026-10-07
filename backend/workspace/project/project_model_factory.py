from __future__ import annotations

from pathlib import Path
from backend.workspace.path_normalizer import normalize_workspace_path
from uuid import uuid4

from backend.workspace.project.project_descriptor import (
    ProjectDescriptor,
)
from backend.workspace.project.project_model import (
    ProjectModel,
)


class ProjectModelFactory:
    """
    Pure project-model construction boundary.

    Owns:
        - input normalization
        - canonical project-root normalization
        - project-id generation
        - ProjectModel construction

    Does not own:
        - workspace construction
        - filesystem access
        - persistence
        - execution
        - agent lifecycle
    """

    VERSION = "1.1"

    def create(
        self,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ProjectModel:
        if not isinstance(name, str):
            raise TypeError("project name must str")

        if not isinstance(root_path, str):
            raise TypeError("project root path must str")

        normalized_name = name.strip()
        normalized_root = normalize_workspace_path(root_path.strip())

        if not normalized_name:
            raise ValueError("project name required")

        if not normalized_root:
            raise ValueError("project root path required")

        canonical_root = str(
            Path(normalized_root)
            .expanduser()
            .resolve()
        )

        resolved_id = ""

        if project_id is not None:
            if not isinstance(project_id, str):
                raise TypeError(
                    "project_id must str or None"
                )

            resolved_id = project_id.strip()

            if not resolved_id:
                raise ValueError(
                    "project_id cannot be empty"
                )

        if not resolved_id:
            resolved_id = f"prj_{uuid4().hex}"

        if workspace_id is not None:
            if not isinstance(workspace_id, str):
                raise TypeError(
                    "workspace_id must str or None"
                )

            workspace_id = workspace_id.strip()

            if not workspace_id:
                raise ValueError(
                    "workspace_id cannot be empty"
                )

        return ProjectModel(
            ProjectDescriptor(
                project_id=resolved_id,
                name=normalized_name,
                root_path=canonical_root,
                workspace_id=workspace_id,
            )
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectModelFactory",
]
