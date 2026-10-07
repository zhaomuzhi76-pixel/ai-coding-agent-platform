from __future__ import annotations

import hashlib
from typing import Any

from backend.code_intelligence.patch_path import PatchPathBoundary

class PatchExecutor:
    """
    Coordinate patch validation, backup, stale-content checking,
    and writing.
    """

    VERSION = "11.2"
    RESPONSIBILITY = (
        "industrial_patch_execution",
    )

    def __init__(
        self,
        writer: Any,
        validator: Any,
        backup: Any,
        path_boundary: PatchPathBoundary | None = None,
    ) -> None:
        for name, value in (
            ("writer", writer),
            ("validator", validator),
            ("backup", backup),
        ):
            if value is None:
                raise ValueError(f"{name} required")

        self.writer = writer
        self.validator = validator
        self.backup = backup
        self.path_boundary = (
            path_boundary or PatchPathBoundary()
        )

        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0

    def execute(
        self,
        patch: dict[str, Any],
        *,
        root: str = ".",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        self.execution_count += 1

        validation = self.validator.validate(
            patch,
            root=root,
        )
        if not validation.get("success", False):
            return self._failed("validation", validation)

        try:
            target = self.path_boundary.resolve(
                root,
                patch["file"],
            )
        except (TypeError, ValueError) as error:
            return self._failed(
                "path",
                {
                    "success": False,
                    "error": "unsafe_path",
                    "detail": str(error),
                },
            )

        if not target.exists() or not target.is_file():
            return self._failed(
                "target",
                {
                    "success": False,
                    "error": "file_not_found",
                },
            )

        try:
            current = target.read_text(encoding="utf-8")
        except Exception as error:
            return self._failed(
                "read",
                {
                    "success": False,
                    "error": "read_failed",
                    "detail": str(error),
                },
            )

        expected = patch["old_content"]
        if current != expected:
            return self._failed(
                "stale_content",
                {
                    "success": False,
                    "error": "old_content_mismatch",
                    "expected_hash": self._hash(expected),
                    "current_hash": self._hash(current),
                },
            )

        backup = self.backup.create(
            patch,
            root=root,
        )
        if not backup.get("success", False):
            return self._failed("backup", backup)

        if dry_run:
            self.success_count += 1
            return {
                "success": True,
                "stage": "dry_run",
                "file": patch["file"],
                "backup": backup,
            }

        result = self.writer.write(
            str(target),
            patch["replacement"],
        )
        if not result.get("success", False):
            return self._failed("write", result)

        self.success_count += 1
        return {
            "success": True,
            "stage": "completed",
            "file": patch["file"],
            "target": str(target),
            "backup": backup,
            "writer": result,
        }

    def ready(self) -> bool:
        return all(
            (
                self.writer is not None,
                self.validator is not None,
                self.backup is not None,
                self.path_boundary.ready(),
            )
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "components": {
                "writer": type(self.writer).__name__,
                "validator": type(self.validator).__name__,
                "backup": type(self.backup).__name__,
            },
            "metrics": {
                "executions": self.execution_count,
                "success": self.success_count,
                "failure": self.failure_count,
            },
        }

    def _failed(
        self,
        stage: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        self.failure_count += 1
        return {
            "success": False,
            "stage": stage,
            "result": result,
        }

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

__all__ = [
    "PatchExecutor",
]
