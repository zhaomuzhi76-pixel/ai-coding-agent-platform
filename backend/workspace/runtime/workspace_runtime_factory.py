from __future__ import annotations

from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)
from backend.workspace.runtime.workspace_runtime import (
    WorkspaceRuntime,
)
from backend.workspace.runtime_binding import (
    WorkspaceRuntimeBinding,
)


class WorkspaceRuntimeFactory(WorkspaceRuntimeFactoryContract):
    """
    Workspace runtime construction boundary.

    Responsibility:
        - validate workspace root
        - construct WorkspaceRuntimeBinding
        - construct WorkspaceRuntime
        - expose workspace runtime construction diagnostics

    Not Responsible:
        - application lifecycle
        - tool construction
        - provider construction
        - filesystem business operations
        - workspace runtime execution
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "workspace_runtime_construction",
    )

    def create(
        self,
        root_path: str,
    ) -> WorkspaceRuntimeContract:
        if not isinstance(root_path, str):
            raise TypeError(
                "workspace root path must be str"
            )

        root_path = root_path.strip()

        if not root_path:
            raise ValueError(
                "workspace root path required"
            )

        binding = WorkspaceRuntimeBinding(
            root_path=root_path,
        )

        if not binding.ready():
            raise RuntimeError(
                "workspace runtime binding unavailable"
            )

        runtime = WorkspaceRuntime(
            binding=binding,
        )

        if not runtime.ready():
            runtime.close()
            raise RuntimeError(
                "workspace runtime unavailable"
            )

        return runtime

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "WorkspaceRuntimeFactory",
]
