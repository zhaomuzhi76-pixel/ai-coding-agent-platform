from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.code_intelligence.patch_path import (
    PatchPathBoundary,
)
from backend.code_intelligence.patch_snapshot import (
    PatchSnapshot,
)

class PatchRollback:
    """
    Patch rollback execution service.

    Responsibility:
        - restore file content from snapshot
        - execute rollback operation
        - return rollback result

    Not Responsible:
        - snapshot creation
        - backup management
        - patch generation
        - patch execution
        - verification
        - repair
    """

    VERSION = "2.1"

    RESPONSIBILITY = (
        "industrial_patch_rollback"
    )

    def __init__(
        self,
        snapshot: PatchSnapshot | None = None,
        path_boundary: PatchPathBoundary | None = None,
    ) -> None:

        self.snapshot = (
            snapshot
            or PatchSnapshot()
        )
        self.path_boundary = (
            path_boundary
            or PatchPathBoundary()
        )

        self.rollback_count = 0
        self.success_count = 0
        self.failure_count = 0

    def rollback(
        self,
        snapshot: dict[str, Any],
        *,
        root: str,
    ) -> dict[str, Any]:

        self.rollback_count += 1

        if not isinstance(
            snapshot,
            dict,
        ):
            return self._failed(
                "invalid_snapshot",
            )

        file = snapshot.get(
            "file",
            "",
        )

        if not file:
            return self._failed(
                "missing_file",
            )

        content = snapshot.get(
            "content",
            "",
        )

        try:
            path = self.path_boundary.resolve_snapshot(
                root,
                file,
            )
            path.write_text(
                str(content),
                encoding="utf-8",
            )

        except Exception as exc:

            return self._failed(
                "write_failed",
                detail=str(exc),
            )

        self.success_count += 1

        return {
            "success": True,
            "file": file,
            "operation": "rollback",
        }

    def _failed(
        self,
        error: str,
        **data: Any,
    ) -> dict[str, Any]:

        self.failure_count += 1

        return {
            "success": False,
            "error": error,
            **data,
        }

    def ready(
        self,
    ) -> bool:

        return (
            self.snapshot.ready()
            and self.path_boundary.ready()
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "PatchRollback",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "snapshot":
                type(
                    self.snapshot
                ).__name__,
            "path_boundary":
                type(
                    self.path_boundary
                ).__name__,

            "metrics": {
                "rollback":
                    self.rollback_count,

                "success":
                    self.success_count,

                "failure":
                    self.failure_count,
            },

            "capabilities": [
                "snapshot_restore",
                "content_recovery",
            ],
        }

__all__ = [
    "PatchRollback",
]
