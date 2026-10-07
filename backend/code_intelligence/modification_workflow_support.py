from __future__ import annotations

from typing import Any

from backend.code_intelligence.modification_transaction import (
    ModificationTransaction,
)
from backend.code_intelligence.patch_path import PatchPathBoundary
from backend.code_intelligence.patch_rollback import PatchRollback

class ModificationWorkflowSupport:
    """
    Shared support for transactional modification workflows.

    Owns:
        - patch preparation
        - patch execution dispatch
        - verification aggregation
        - rollback dispatch
    """

    VERSION = "1.6"

    def __init__(self, rollback: PatchRollback) -> None:
        if rollback is None:
            raise ValueError("rollback required")
        self._rollback_service = rollback

    def extract_patches(
        self,
        bundle: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(bundle, dict):
            raise TypeError("patch generator must return dict")

        patches = bundle.get("patches", [])
        if not isinstance(patches, list):
            raise TypeError("patch bundle patches must list")

        result = []
        for index, patch in enumerate(patches):
            if not isinstance(patch, dict):
                raise TypeError(f"patches[{index}] must dict")
            if not patch.get("file"):
                raise ValueError(
                    f"patches[{index}] file required"
                )
            result.append(patch)

        return result

    def generate_patches(
        self,
        generator: Any,
        plan: dict[str, Any],
        changes: dict[str, Any],
        root: str,
    ) -> list[dict[str, Any]]:
        bundle = generator.generate(
            plan,
            changes=changes,
            root=root,
        )
        return self.extract_patches(bundle)

    def execute_patches(
        self,
        executor: Any,
        patches: list[dict[str, Any]],
        root: str,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        bool,
    ]:
        executions = []
        snapshots = []

        for patch in patches:
            result = executor.execute(
                patch,
                root=root,
            )
            executions.append(result)

            snapshot = self.collect_snapshot(result)
            if snapshot is not None:
                snapshots.append(snapshot)

            if not result.get("success", False):
                return executions, snapshots, False

        return executions, snapshots, True

    @staticmethod
    def collect_snapshot(
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        backup = result.get("backup", {})
        if not isinstance(backup, dict):
            return None

        snapshot = backup.get("snapshot")
        return (
            snapshot
            if isinstance(snapshot, dict)
            else None
        )

    def verify(
        self,
        verifier: Any,
        files: list[str],
        root: str,
    ) -> dict[str, Any]:
        results = []

        for file in files:
            resolved = PatchPathBoundary().resolve(
                root,
                file,
            )
            results.append(
                verifier.verify(
                    file=str(resolved)
                )
            )

        return {
            "success": all(
                item.get("success", False)
                for item in results
            ),
            "results": results,
        }

    def rollback(
        self,
        snapshots: list[dict[str, Any]],
        *,
        root: str,
    ) -> list[dict[str, Any]]:
        results = []
        for snapshot in reversed(snapshots):
            results.append(
                self._rollback_service.rollback(
                    snapshot,
                    root=root,
                )
            )
        return results

    def ready(self) -> bool:
        return (
            self._rollback_service is not None
            and self._rollback_service.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "rollback": type(
                self._rollback_service
            ).__name__,
        }

__all__ = ["ModificationWorkflowSupport"]
