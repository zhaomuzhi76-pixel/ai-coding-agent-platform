from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any

from backend.code_intelligence.patch_path import (
    PatchPathBoundary,
)

class PatchGenerator:
    """
    Code patch generation service.

    Responsibility:
        - generate patch description
        - capture source snapshot
        - create patch identity

    Not Responsible:
        - planning
        - impact analysis
        - patch validation
        - patch execution
        - backup
        - rollback
        - verification
    """

    VERSION = "4.0"

    RESPONSIBILITY = (
        "code_patch_generation"
    )

    def generate(
        self,
        plan: dict[str, Any],
        changes: dict[str, Any] | None = None,
        *,
        root: str = ".",
    ) -> dict[str, Any]:

        changes = changes or {}

        patches = [
            self._create_patch(
                file=file,
                change=changes.get(
                    file,
                    {},
                ),
                risk=plan.get(
                    "risk",
                    "unknown",
                ),
                root=root,
            )
            for file in plan.get(
                "files",
                [],
            )
        ]

        return {
            "task": plan.get(
                "task",
                "",
            ),
            "patches": patches,
            "count": len(patches),
        }

    def _create_patch(
        self,
        *,
        file: str,
        change: dict[str, Any],
        risk: str,
        root: str,
    ) -> dict[str, Any]:

        path = PatchPathBoundary().resolve(
            root,
            file,
        )

        old_content = ""

        if path.exists():
            old_content = path.read_text(
                encoding="utf-8",
            )

        replacement = change.get(
            "replacement",
        )

        if not isinstance(
            replacement,
            str,
        ):
            raise ValueError(
                f"replacement required: {file}"
            )

        if replacement == old_content:
            raise ValueError(
                f"no-op modification rejected: {file}"
            )

        patch = {
            "file": file,
            "operation": "replace",
            "old_content": old_content,
            "replacement": replacement,
            "reason": change.get(
                "reason",
                "",
            ),
            "risk": risk,
        }

        patch["patch_id"] = (
            self._create_id(
                patch,
            )
        )

        return patch

    def _create_id(
        self,
        patch: dict[str, Any],
    ) -> str:

        value = (
            patch["file"]
            + patch["old_content"]
            + patch["replacement"]
        )

        return hashlib.sha256(
            value.encode(
                "utf-8",
            )
        ).hexdigest()[:16]

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "PatchGenerator",
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "ready":
                self.ready(),
        }

__all__ = [
    "PatchGenerator",
]
