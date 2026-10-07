from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.code_intelligence.modification_execution_support import (
    ModificationExecutionSupport,
)
from backend.code_intelligence.modification_transaction import ModificationTransaction
from backend.code_intelligence.modification_workflow_support import ModificationWorkflowSupport


class ModificationWorkflow:
    VERSION = "15.0"
    RESPONSIBILITY = ("transactional_modification_workflow",)

    def __init__(
        self,
        planner: Any,
        patch_generator: Any,
        patch_executor: Any,
        verifier: Any,
        rollback: Any,
        support: ModificationWorkflowSupport | None = None,
        execution_support: ModificationExecutionSupport | None = None,
    ) -> None:
        for name, value in (
            ("planner", planner),
            ("patch_generator", patch_generator),
            ("patch_executor", patch_executor),
            ("verifier", verifier),
            ("rollback", rollback),
        ):
            if value is None:
                raise ValueError(f"{name} required")
        self.planner = planner
        self.patch_generator = patch_generator
        self.patch_executor = patch_executor
        self.verifier = verifier
        self.support = support or ModificationWorkflowSupport(rollback)
        self.execution_support = (
            execution_support or ModificationExecutionSupport(self.support)
        )
        self.total = 0
        self.success = 0
        self.failure = 0
        self.stage = "created"

    def execute(
        self,
        *,
        task: str,
        files: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate(task, files)
        self.total += 1
        transaction = ModificationTransaction(str(uuid4()))
        executions: list[dict[str, Any]] = []
        snapshots: list[dict[str, Any]] = []
        runtime = dict(context or {})
        root_value = runtime.get("root")
        if not isinstance(root_value, str) or not root_value.strip():
            raise ValueError(
                "modification root required"
            )
        root = root_value.strip()

        try:
            transaction.prepare()
            plan = self.planner.plan(
                task=task,
                context=runtime,
            )

            if not isinstance(plan, dict):
                return self._abort(
                    transaction,
                    executions,
                    snapshots,
                    "planning",
                    "modification plan must dict",
                    root,
                )

            changes = runtime.get("changes")
            if changes is None:
                changes = plan.get("changes", {})
            if not isinstance(changes, dict) or not changes:
                return self._abort(
                    transaction, executions, snapshots,
                    "generation", "no modification changes supplied", root
                )
            plan_files = plan.get("files", [])
            if isinstance(plan_files, list):
                missing = [
                    file
                    for file in plan_files
                    if file not in changes
                ]
                if missing:
                    return self._abort(
                        transaction,
                        executions,
                        snapshots,
                        "generation",
                        "modification changes missing for: "
                        + ", ".join(map(str, missing)),
                        root,
                    )

            try:
                patches = self.support.generate_patches(
                    self.patch_generator, plan, changes, root
                )
            except Exception as error:
                return self._abort(
                    transaction, executions, snapshots,
                    "generation", str(error), root
                )
            if not patches:
                return self._abort(
                    transaction, executions, snapshots,
                    "generation", "no patches generated", root
                )

            transaction.start()
            self.stage = "execution"
            executions, snapshots, executed = self.execution_support.execute(
                executor=self.patch_executor,
                patches=patches,
                root=root,
            )
            if not executed:
                return self._abort(
                    transaction, executions, snapshots,
                    self.stage, "patch execution failed", root
                )

            transaction.verify()
            self.stage = "verification"
            verification = self.execution_support.verify(
                verifier=self.verifier,
                files=files,
                root=root,
            )
            if not verification["success"]:
                return self._abort(
                    transaction, executions, snapshots,
                    self.stage, "verification failed", root, verification
                )

            transaction.commit()
            self.success += 1
            self.stage = "completed"
            return self.execution_support.result(
                transaction, self.stage, executions, verification
            )

        except Exception as error:
            self.failure += 1
            self.stage = "failed"
            self.execution_support.rollback(snapshots, root=root)
            if transaction.state not in (
                transaction.COMMITTED, transaction.ABORTED
            ):
                transaction.abort(str(error))
            raise

    def _abort(
        self,
        transaction: ModificationTransaction,
        executions: list[dict[str, Any]],
        snapshots: list[dict[str, Any]],
        stage: str,
        reason: str,
        root: str,
        verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.failure += 1
        self.stage = stage
        return self.execution_support.abort(
            transaction=transaction,
            executions=executions,
            snapshots=snapshots,
            stage=stage,
            reason=reason,
            root=root,
            verification=verification,
        )

    @staticmethod
    def _validate(task: str, files: list[str]) -> None:
        if not task:
            raise ValueError("modification task required")
        if not files:
            raise ValueError("modification files required")

    def ready(self) -> bool:
        return all((
            self.planner is not None,
            self.patch_generator is not None,
            self.patch_executor is not None,
            self.verifier is not None,
            self.support.ready(),
            self.execution_support.ready(),
        ))

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "stage": self.stage,
            "metrics": {
                "total": self.total,
                "success": self.success,
                "failure": self.failure,
            },
            "support": self.support.dump(),
            "execution_support": self.execution_support.dump(),
        }


__all__ = ["ModificationWorkflow"]
