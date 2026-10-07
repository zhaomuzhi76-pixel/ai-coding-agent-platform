from __future__ import annotations

from typing import Any

from backend.code_intelligence.modification_transaction import (
    ModificationTransaction,
)
from backend.code_intelligence.modification_workflow_support import (
    ModificationWorkflowSupport,
)

class ModificationExecutionSupport:
    """
    Transactional execution boundary.

    Owns:
        - patch execution
        - verification delegation
        - abort/rollback
        - terminal result shaping
    """

    VERSION = "1.3"

    def __init__(
        self,
        support: ModificationWorkflowSupport,
    ) -> None:
        if support is None:
            raise ValueError(
                "workflow support required"
            )
        self.support = support

    def execute(
        self,
        *,
        executor: Any,
        patches: list[dict[str, Any]],
        root: str,
    ):
        return self.support.execute_patches(
            executor,
            patches,
            root,
        )

    def verify(
        self,
        *,
        verifier: Any,
        files: list[str],
        root: str,
    ) -> dict[str, Any]:
        return self.support.verify(
            verifier,
            files,
            root,
        )

    def abort(
        self,
        *,
        transaction: ModificationTransaction,
        executions: list[dict[str, Any]],
        snapshots: list[dict[str, Any]],
        stage: str,
        reason: str,
        root: str,
        verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.support.rollback(
            snapshots,
            root=root,
        )

        if transaction.state not in (
            transaction.COMMITTED,
            transaction.ABORTED,
        ):
            transaction.abort(reason)

        return self.result(
            transaction,
            stage,
            executions,
            verification,
        )

    @staticmethod
    def result(
        transaction: ModificationTransaction,
        stage: str,
        executions: list[dict[str, Any]],
        verification: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "success": (
                transaction.state
                == transaction.COMMITTED
            ),
            "stage": stage,
            "transaction": transaction.dump(),
            "execution": executions,
            "verification": verification,
        }

    def rollback(
        self,
        snapshots: list[dict[str, Any]],
        *,
        root: str,
    ) -> list[dict[str, Any]]:
        return self.support.rollback(
            snapshots,
            root=root,
        )

    def ready(self) -> bool:
        return self.support.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "support": self.support.__class__.__name__,
        }

__all__ = ["ModificationExecutionSupport"]
