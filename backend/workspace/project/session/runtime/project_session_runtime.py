from __future__ import annotations

from typing import Any

from backend.workspace.project.runtime.project_runtime_contract import (
    ProjectRuntimeContract,
)
from backend.workspace.project.session.project_session_model import (
    ProjectSessionModel,
)
from backend.workspace.project.session.runtime.project_session_runtime_binding import (
    ProjectSessionRuntimeBinding,
)
from backend.workspace.project.session.runtime.project_session_runtime_contract import (
    ProjectSessionRuntimeContract,
)
from backend.workspace.project.session.runtime.project_session_runtime_state import (
    ProjectSessionRuntimeState,
)


class ProjectSessionRuntime(ProjectSessionRuntimeContract):
    """
    Active programming-project session runtime.

    Owns:
        - session runtime lifecycle
        - access to project runtime capabilities

    Does not own:
        - workspace construction
        - project construction
        - persistence
        - registry coordination
        - execution policy
        - agent orchestration
    """

    VERSION = "1.0"

    def __init__(
        self,
        binding: ProjectSessionRuntimeBinding,
    ) -> None:
        if not isinstance(
            binding,
            ProjectSessionRuntimeBinding,
        ):
            raise TypeError(
                "binding must "
                "ProjectSessionRuntimeBinding"
            )

        self.binding = binding
        self.state = (
            ProjectSessionRuntimeState.CREATED
        )

    @property
    def session(
        self,
    ) -> ProjectSessionModel:
        return self.binding.get_session()

    @property
    def project_runtime(
        self,
    ) -> ProjectRuntimeContract:
        return self.binding.get_project_runtime()

    @property
    def session_id(
        self,
    ) -> str:
        return self.session.session_id

    @property
    def project_id(
        self,
    ) -> str:
        return self.session.project_id

    @property
    def root_path(
        self,
    ) -> str:
        return self.session.root_path

    def start(
        self,
    ) -> None:
        if (
            self.state
            is ProjectSessionRuntimeState.CLOSED
        ):
            raise RuntimeError(
                "closed project session runtime "
                "cannot start"
            )

        if not self.project_runtime.ready():
            raise RuntimeError(
                "project runtime not ready"
            )

        if self.session.state.value == "closed":
            raise RuntimeError(
                "closed project session cannot start"
            )

        if not self.session.ready():
            self.session.start()

        if not self.session.ready():
            raise RuntimeError(
                "project session unavailable"
            )

        self.state = (
            ProjectSessionRuntimeState.ACTIVE
        )

    def close(
        self,
    ) -> None:
        if (
            self.state
            is ProjectSessionRuntimeState.CLOSED
        ):
            return

        try:
            self.session.close()
        finally:
            self.project_runtime.close()
            self.state = (
                ProjectSessionRuntimeState.CLOSED
            )

    def get_filesystem(
        self,
    ) -> Any:
        self._require_ready()
        return self.project_runtime.get_filesystem()

    def get_index(
        self,
    ) -> Any:
        self._require_ready()
        return self.project_runtime.get_index()

    def get_query(
        self,
    ) -> Any:
        self._require_ready()
        return self.project_runtime.get_query()

    def get_operations(
        self,
    ) -> Any:
        self._require_ready()
        return self.project_runtime.get_operations()

    def _require_ready(
        self,
    ) -> None:
        if not self.ready():
            raise RuntimeError(
                "project session runtime not ready"
            )

    def ready(
        self,
    ) -> bool:
        return (
            self.binding.ready()
            and self.state.ready()
            and self.session.ready()
            and self.project_runtime.ready()
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
            "root_path":
                self.root_path,
            "state":
                self.state.value,
            "ready":
                self.ready(),
            "binding":
                self.binding.dump(),
        }


__all__ = [
    "ProjectSessionRuntime",
]
