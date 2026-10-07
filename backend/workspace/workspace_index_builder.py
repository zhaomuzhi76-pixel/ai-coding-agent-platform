from __future__ import annotations

from backend.workspace.workspace_index import (
    WorkspaceIndex,
)
from backend.workspace.workspace_scanner import (
    WorkspaceScanner,
)


class WorkspaceIndexBuilder:
    """
    Workspace scan-to-index composition boundary.

    Responsibility:
        - validate scan/index dependencies
        - execute workspace scan
        - populate WorkspaceIndex
        - expose build diagnostics

    Does not own:
        - filesystem scanning implementation
        - index query semantics
        - repository operations
        - workspace lifecycle
    """

    VERSION = "1.1"
    RESPONSIBILITY = (
        "workspace_index_construction",
    )

    def __init__(
        self,
        scanner: WorkspaceScanner,
        index: WorkspaceIndex,
    ) -> None:
        if scanner is None:
            raise ValueError(
                "workspace scanner required"
            )

        if index is None:
            raise ValueError(
                "workspace index required"
            )

        self.scanner = scanner
        self.index = index
        self.build_count = 0

    def build(
        self,
    ) -> int:
        self._validate_dependencies()

        items = self.scanner.scan()

        self.index.reset(
            str(self.scanner.root)
        )

        for metadata in items:
            self.index.add(
                metadata
            )

        self.build_count += 1

        if not self.index.ready():
            raise RuntimeError(
                "workspace index build incomplete"
            )

        return len(items)

    def ready(
        self,
    ) -> bool:
        """
        Builder readiness is a pre-build capability check.

        The index itself does not need to be ready before the
        builder performs its first construction pass.
        """
        return (
            self.scanner is not None
            and self.index is not None
            and self.scanner.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "build_count": self.build_count,
            "scanner": self.scanner.dump(),
            "index": self.index.dump(),
        }

    def _validate_dependencies(
        self,
    ) -> None:
        if not self.ready():
            raise RuntimeError(
                "workspace index builder unavailable"
            )


__all__ = [
    "WorkspaceIndexBuilder",
]
