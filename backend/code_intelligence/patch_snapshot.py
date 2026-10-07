from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.utils.time import now_iso

class PatchSnapshot:
    """
    Patch rollback snapshot data model.

    Responsibility:
        - define snapshot structure
        - create snapshot payload
        - validate snapshot integrity

    Not Responsible:
        - file backup
        - file restore
        - patch execution
        - patch validation workflow
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "code_patch_snapshot_model"
    )

    def create(
        self,
        *,
        file: str,
        content: str,
        hash_value: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "snapshot_id":
                str(
                    uuid4()
                ),

            "snapshot_version":
                self.VERSION,

            "file":
                file,

            "content":
                content,

            "hash":
                hash_value,

            "metadata":
                metadata or {},

            "created_at":
                now_iso(),
        }

    def validate(
        self,
        snapshot: dict[str, Any],
    ) -> bool:

        required = (
            "snapshot_id",
            "file",
            "content",
            "created_at",
        )

        return all(
            item in snapshot
            for item in required
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name":
                "PatchSnapshot",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "schema":
                [
                    "snapshot_id",
                    "file",
                    "content",
                    "hash",
                    "metadata",
                    "created_at",
                ],
        }

__all__ = [
    "PatchSnapshot",
]
