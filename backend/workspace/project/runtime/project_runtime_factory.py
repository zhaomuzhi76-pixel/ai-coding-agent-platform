from __future__ import annotations

from pathlib import Path
from backend.workspace.path_normalizer import normalize_workspace_path

from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)
from backend.workspace.project.project_model_factory import (
    ProjectModelFactory,
)
from backend.workspace.project.runtime.project_runtime import (
    ProjectRuntime,
)
from backend.workspace.project.runtime.project_runtime_binding import (
    ProjectRuntimeBinding,
)
from backend.workspace.project.runtime.project_runtime_contract import (
    ProjectRuntimeContract,
)
from backend.workspace.project.runtime.workspace_runtime_projection import (
    WorkspaceRuntimeProjection,
)


class ProjectRuntimeFactory:
    """
    Project runtime construction boundary.
    """

    VERSION = "1.5"

    def __init__(
        self,
        *,
        project_factory: ProjectModelFactory,
        workspace_factory: WorkspaceRuntimeFactoryContract,
    ) -> None:
        if not isinstance(
            project_factory,
            ProjectModelFactory,
        ):
            raise TypeError(
                "project factory required"
            )

        if not isinstance(
            workspace_factory,
            WorkspaceRuntimeFactoryContract,
        ):
            raise TypeError(
                "workspace factory contract required"
            )

        self.project_factory = project_factory
        self.workspace_factory = workspace_factory

    def create(
        self,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ProjectRuntimeContract:
        if not self.ready():
            raise RuntimeError(
                "project runtime factory unavailable"
            )

        if not isinstance(
            root_path,
            str,
        ):
            raise TypeError(
                "project root path must str"
            )

        normalized_root = normalize_workspace_path(root_path.strip())

        if not normalized_root:
            raise ValueError(
                "project root path required"
            )

        canonical_root = str(
            Path(normalized_root)
            .expanduser()
            .resolve()
        )

        project = self.project_factory.create(
            name=name,
            root_path=canonical_root,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        workspace_runtime = (
            self.workspace_factory.create(
                canonical_root
            )
        )

        try:
            workspace = WorkspaceRuntimeProjection(
                workspace_runtime
            )

            binding = ProjectRuntimeBinding(
                project=project,
                workspace=workspace,
            )

            if not binding.ready():
                raise RuntimeError(
                    "project runtime binding unavailable"
                )

            runtime = ProjectRuntime(
                binding=binding
            )
            runtime.start()

            if not isinstance(
                runtime,
                ProjectRuntimeContract,
            ):
                runtime.close()
                raise TypeError(
                    "project runtime contract violation"
                )

            if not runtime.ready():
                runtime.close()
                raise RuntimeError(
                    "project runtime unavailable"
                )

            return runtime

        except Exception:
            workspace_runtime.close()
            raise

    def ready(self) -> bool:
        return (
            self.project_factory.ready()
            and self.workspace_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "project_factory":
                self.project_factory.dump(),
            "workspace_factory":
                self.workspace_factory.dump(),
        }


__all__ = [
    "ProjectRuntimeFactory",
]
