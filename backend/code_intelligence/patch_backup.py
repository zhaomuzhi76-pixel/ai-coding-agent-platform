from __future__ import annotations

from typing import Any

from backend.code_intelligence.patch_path import PatchPathBoundary
from backend.code_intelligence.patch_snapshot import PatchSnapshot


class PatchBackup:
    """
    Patch backup creation service.

    Responsibility:
        - capture original file content
        - create rollback snapshot

    Not Responsible:
        - snapshot storage
        - patch generation
        - patch execution
        - restore execution
        - verification
    """

    VERSION = "6.0"
    RESPONSIBILITY = (
        "industrial_patch_backup",
    )

    def __init__(
        self,
        snapshot: PatchSnapshot | None = None,
        path_boundary: PatchPathBoundary | None = None,
    ) -> None:
        self.snapshot = snapshot or PatchSnapshot()
        self.path_boundary = path_boundary or PatchPathBoundary()

    def create(
        self,
        patch: dict[str, Any],
        *,
        root: str = ".",
    ) -> dict[str, Any]:
        if not isinstance(patch, dict):
            return self._error("invalid_patch")

        file = patch.get("file", "")
        if not isinstance(file, str) or not file:
            return self._error("missing_file")

        try:
            path = self.path_boundary.resolve(root, file)
        except (TypeError, ValueError) as error:
            return self._error(
                "unsafe_path",
                file=file,
                detail=str(error),
            )

        if not path.exists():
            return self._error(
                "file_not_found",
                file=str(path),
            )

        if not path.is_file():
            return self._error(
                "not_a_file",
                file=str(path),
            )

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            return self._error(
                "read_failed",
                detail=str(exc),
            )

        snapshot = self.snapshot.create(
            file=str(path),
            content=content,
        )

        return {
            "success": True,
            "file": file,
            "target": str(path),
            "snapshot": snapshot,
        }

    def ready(self) -> bool:
        return (
            self.snapshot.ready()
            and self.path_boundary.ready()
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "snapshot": type(self.snapshot).__name__,
            "path_boundary": type(
                self.path_boundary
            ).__name__,
        }

    @staticmethod
    def _error(
        error: str,
        **data: Any,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "error": error,
            **data,
        }


__all__ = [
    "PatchBackup",
]
