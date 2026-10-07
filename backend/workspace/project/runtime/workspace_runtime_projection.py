from __future__ import annotations

from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)


class WorkspaceRuntimeProjection(
    WorkspaceRuntimeContract,
):
    """
    Project-layer projection of the frozen workspace contract.

    Owns:
        - expose the frozen workspace runtime contract

    Does not own:
        - filesystem implementation
        - index implementation
        - repository implementation
        - workspace scanning
        - workspace lifecycle construction
        - execution
        - persistence
    """

    VERSION = "1.1"

    def __init__(
        self,
        runtime: WorkspaceRuntimeContract,
    ) -> None:
        if not isinstance(
            runtime,
            WorkspaceRuntimeContract,
        ):
            raise TypeError(
                "workspace runtime contract required"
            )

        self._runtime = runtime

    @property
    def workspace_id(
        self,
    ) -> str | None:
        return self._runtime.workspace_id

    @property
    def root_path(
        self,
    ) -> str:
        return self._runtime.root_path

    def get_context(
        self,
    ) -> object:
        return self._runtime.get_context()

    def get_service(
        self,
    ) -> object:
        return self._runtime.get_service()

    def get_repository(
        self,
    ) -> object:
        return self._runtime.get_repository()

    def get_filesystem(
        self,
    ) -> object:
        return self._runtime.get_filesystem()

    def get_index(
        self,
    ) -> object:
        return self._runtime.get_index()

    def get_query(
        self,
    ) -> object:
        return self._runtime.get_query()

    def get_operations(
        self,
    ) -> object:
        return self._runtime.get_operations()

    def close(
        self,
    ) -> None:
        self._runtime.close()

    def ready(
        self,
    ) -> bool:
        return self._runtime.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "root_path": self.root_path,
            "workspace_id": self.workspace_id,
            "runtime": type(
                self._runtime
            ).__name__,
        }


__all__ = [
    "WorkspaceRuntimeProjection",
]
