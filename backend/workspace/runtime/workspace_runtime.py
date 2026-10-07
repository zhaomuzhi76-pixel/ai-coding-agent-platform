from __future__ import annotations

from typing import Any

from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)
from backend.workspace.runtime.workspace_runtime_state import (
    WorkspaceRuntimeState,
)
from backend.workspace.runtime_binding import (
    WorkspaceRuntimeBinding,
)


class WorkspaceRuntime(WorkspaceRuntimeContract):
    """
    Active workspace runtime boundary.

    Responsibility:
        - hold active workspace runtime
        - expose bound workspace capabilities
        - manage runtime open/close state

    Not Responsible:
        - workspace creation
        - filesystem operations
        - scanning
        - indexing
        - analysis
        - intelligence generation
    """

    VERSION = "2.3"

    RESPONSIBILITY = (
        "workspace_runtime",
    )

    def __init__(
        self,
        binding: WorkspaceRuntimeBinding,
        state: WorkspaceRuntimeState | None = None,
    ) -> None:
        if not isinstance(
            binding,
            WorkspaceRuntimeBinding,
        ):
            raise TypeError(
                "binding must be WorkspaceRuntimeBinding"
            )

        self.binding = binding
        self.state = (
            state
            or WorkspaceRuntimeState()
        )
        self.state.open(
            self.root_path
        )

    @property
    def root_path(self) -> str:
        return self.binding.get_context().root_path

    @property
    def workspace_id(self) -> str | None:
        return self.binding.get_context().workspace_id

    def ready(self) -> bool:
        return (
            self.binding.ready()
            and self.state.ready()
        )

    def get_context(self) -> Any:
        self._require_ready()
        return self.binding.get_context()

    def get_service(self) -> Any:
        self._require_ready()
        return self.binding.get_service()

    def get_repository(self) -> Any:
        self._require_ready()
        return self.binding.get_repository()

    def get_index(self) -> Any:
        self._require_ready()
        return self.binding.get_index()

    def get_query(self) -> Any:
        self._require_ready()
        return self.binding.get_query()

    def get_filesystem(self) -> Any:
        self._require_ready()
        return self.binding.get_filesystem()

    def get_operations(self) -> Any:
        self._require_ready()
        return self.binding.get_operations()

    def _require_ready(self) -> None:
        if not self.ready():
            raise RuntimeError(
                "workspace runtime not ready"
            )

    def close(self) -> None:
        self.state.close()

    def dump(self) -> dict[str, Any]:
        return {
            "name": "WorkspaceRuntime",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "root": self.root_path,
            "state": self.state.dump(),
            "binding": self.binding.dump(),
        }


__all__ = [
    "WorkspaceRuntime",
]
