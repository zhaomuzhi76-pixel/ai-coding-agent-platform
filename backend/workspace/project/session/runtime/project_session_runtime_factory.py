from __future__ import annotations

from backend.workspace.project.runtime.project_runtime_contract import (
    ProjectRuntimeContract,
)
from backend.workspace.project.runtime.project_runtime_factory import (
    ProjectRuntimeFactory,
)
from backend.workspace.project.session.project_session_model_factory import (
    ProjectSessionModelFactory,
)
from backend.workspace.project.session.runtime.project_session_runtime import (
    ProjectSessionRuntime,
)
from backend.workspace.project.session.runtime.project_session_runtime_binding import (
    ProjectSessionRuntimeBinding,
)
from backend.workspace.project.session.runtime.project_session_runtime_contract import (
    ProjectSessionRuntimeContract,
)
from backend.workspace.project.session.runtime.project_session_runtime_factory_contract import (
    ProjectSessionRuntimeFactoryContract,
)


class ProjectSessionRuntimeFactory(
    ProjectSessionRuntimeFactoryContract,
):
    """
    Project-session runtime construction boundary.
    """

    VERSION = "1.2"

    def __init__(
        self,
        *,
        session_factory: ProjectSessionModelFactory,
        project_runtime_factory: ProjectRuntimeFactory,
    ) -> None:
        if not isinstance(
            session_factory,
            ProjectSessionModelFactory,
        ):
            raise TypeError(
                "session factory required"
            )

        if not isinstance(
            project_runtime_factory,
            ProjectRuntimeFactory,
        ):
            raise TypeError(
                "project runtime factory required"
            )

        self.session_factory = session_factory
        self.project_runtime_factory = (
            project_runtime_factory
        )

    def create(
        self,
        project_id: str,
        root_path: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict | None = None,
    ) -> ProjectSessionRuntimeContract:
        if not self.ready():
            raise RuntimeError(
                "project session runtime factory "
                "unavailable"
            )

        project_runtime = (
            self.project_runtime_factory.create(
                name="project_session",
                root_path=root_path,
                project_id=project_id,
                workspace_id=workspace_id,
            )
        )

        if not isinstance(
            project_runtime,
            ProjectRuntimeContract,
        ):
            project_runtime.close()
            raise TypeError(
                "project runtime contract violation"
            )

        try:
            session = self.session_factory.create(
                project_id=project_runtime.project_id,
                root_path=project_runtime.root_path,
                session_id=session_id,
                workspace_id=workspace_id,
                runtime_id=runtime_id,
                metadata=metadata,
            )

            if session.project_id != project_runtime.project_id:
                raise RuntimeError(
                    "project session identity composition mismatch"
                )

            binding = ProjectSessionRuntimeBinding(
                session=session,
                project_runtime=project_runtime,
            )

            if not binding.ready():
                raise RuntimeError(
                    "project session runtime binding "
                    "unavailable"
                )

            runtime = ProjectSessionRuntime(
                binding=binding
            )
            runtime.start()

            if not isinstance(
                runtime,
                ProjectSessionRuntimeContract,
            ):
                runtime.close()
                raise TypeError(
                    "project session runtime contract violation"
                )

            if not runtime.ready():
                runtime.close()
                raise RuntimeError(
                    "project session runtime "
                    "unavailable"
                )

            return runtime

        except Exception:
            project_runtime.close()
            raise

    def ready(self) -> bool:
        return (
            self.session_factory.ready()
            and self.project_runtime_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "session_factory":
                self.session_factory.dump(),
            "project_runtime_factory":
                self.project_runtime_factory.dump(),
        }


__all__ = [
    "ProjectSessionRuntimeFactory",
]
