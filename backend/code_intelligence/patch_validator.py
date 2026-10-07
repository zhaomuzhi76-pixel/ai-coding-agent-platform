from __future__ import annotations

from typing import Any

from backend.code_intelligence.patch_path import (
    PatchPathBoundary,
)

class PatchValidator:
    """
    Industrial patch safety validation service.

    Responsibility:
        - validate patch contract
        - validate target path safety
        - validate supported operation
        - validate patch plan consistency

    Not Responsible:
        - patch generation
        - patch execution
        - file writing
        - backup
        - rollback
        - verification
    """

    VERSION = "4.0"
    RESPONSIBILITY = (
        "industrial_patch_validation"
    )

    OPERATIONS = ("replace",)

    REQUIRED_FIELDS = (
        "file",
        "operation",
        "old_content",
        "replacement",
    )

    def __init__(
        self,
        path_boundary: PatchPathBoundary | None = None,
    ) -> None:
        self.path_boundary = (
            path_boundary
            or PatchPathBoundary()
        )

    def validate(
        self,
        patch: dict[str, Any],
        *,
        root: str = ".",
    ) -> dict[str, Any]:
        if not isinstance(patch, dict):
            return self._error("invalid_patch")

        contract = self._validate_contract(patch)
        if not contract["success"]:
            return contract

        try:
            target = self.path_boundary.resolve(
                root,
                patch["file"],
            )
        except (TypeError, ValueError) as error:
            return self._error(
                "unsafe_path",
                file=patch["file"],
                detail=str(error),
            )

        return {
            "success": True,
            "file": patch["file"],
            "target": str(target),
            "operation": patch["operation"],
        }

    def validate_plan(
        self,
        patch_plan: dict[str, Any],
        *,
        root: str = ".",
    ) -> dict[str, Any]:
        if not isinstance(patch_plan, dict):
            return self._error("invalid_plan")

        patches = patch_plan.get("patches", [])
        if not isinstance(patches, list):
            return self._error("invalid_patches")

        results = [
            self.validate(patch, root=root)
            for patch in patches
        ]

        return {
            "success": all(
                item.get("success", False)
                for item in results
            ),
            "results": results,
            "count": len(results),
        }

    def _validate_contract(
        self,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        for field in self.REQUIRED_FIELDS:
            if field not in patch:
                return self._error(
                    "missing_field",
                    field=field,
                )

        if patch["operation"] not in self.OPERATIONS:
            return self._error(
                "unsupported_operation",
                operation=patch["operation"],
            )

        if not isinstance(patch["file"], str):
            return self._error("invalid_file_type")

        if not isinstance(
            patch["old_content"],
            str,
        ):
            return self._error(
                "invalid_old_content"
            )

        if not isinstance(
            patch["replacement"],
            str,
        ):
            return self._error(
                "invalid_replacement"
            )

        return {"success": True}

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

    def ready(self) -> bool:
        return self.path_boundary.ready()

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "operations": list(self.OPERATIONS),
            "required_fields": list(
                self.REQUIRED_FIELDS
            ),
        }

__all__ = [
    "PatchValidator",
]
