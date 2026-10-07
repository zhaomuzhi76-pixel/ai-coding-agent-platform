from __future__ import annotations

from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)


class ApplicationWorkspaceComposition:
    """
    Application workspace construction boundary.

    Owns:
        - request workspace runtime construction
        - expose workspace runtime contract

    Does not own:
        - concrete workspace runtime construction
        - filesystem implementation
        - workspace business operations
        - configuration loading
    """

    VERSION = "4.1"

    RESPONSIBILITY = (
        "workspace_runtime_construction",
        "workspace_contract_exposure",
    )

    def __init__(
        self,
        workspace_root: str,
        factory: WorkspaceRuntimeFactoryContract,
    ) -> None:
        if not isinstance(
            workspace_root,
            str,
        ):
            raise TypeError(
                "workspace_root must be str"
            )

        workspace_root = workspace_root.strip()

        if not workspace_root:
            raise ValueError(
                "workspace_root required"
            )

        if not isinstance(
            factory,
            WorkspaceRuntimeFactoryContract,
        ):
            raise TypeError(
                "workspace runtime factory contract required"
            )

        self.workspace_root = workspace_root
        self.factory = factory

    def create(
        self,
    ) -> WorkspaceRuntimeContract:
        if not self.factory.ready():
            raise RuntimeError(
                "workspace runtime factory unavailable"
            )

        runtime = self.factory.create(
            self.workspace_root
        )

        if not isinstance(
            runtime,
            WorkspaceRuntimeContract,
        ):
            close = getattr(runtime, "close", None)
            if callable(close):
                close()
            raise TypeError(
                "workspace runtime contract violation"
            )

        if not runtime.ready():
            runtime.close()
            raise RuntimeError(
                "workspace runtime unavailable"
            )

        return runtime

    def ready(
        self,
    ) -> bool:
        return (
            bool(self.workspace_root)
            and self.factory.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "workspace_root": self.workspace_root,
            "factory": self.factory.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationWorkspaceComposition",
]
