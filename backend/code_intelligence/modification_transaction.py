from __future__ import annotations

from typing import Any

from backend.utils.time import now_iso

class ModificationTransaction:
    """
    Modification transaction lifecycle boundary.

    Owns transaction state and metadata only.
    It does not execute patches or perform rollback.
    """

    VERSION = "1.1"

    CREATED = "CREATED"
    PREPARED = "PREPARED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"

    TRANSITIONS = {
        CREATED: {PREPARED, ABORTED},
        PREPARED: {EXECUTING, ABORTED},
        EXECUTING: {VERIFYING, ABORTED},
        VERIFYING: {COMMITTED, ABORTED},
        COMMITTED: set(),
        ABORTED: set(),
    }

    def __init__(
        self,
        transaction_id: str,
    ) -> None:
        if not transaction_id:
            raise ValueError(
                "transaction_id required"
            )

        self.transaction_id = transaction_id
        self.state = self.CREATED
        self.created_at = now_iso()
        self.completed_at: str | None = None
        self.abort_reason = ""

    def transition(
        self,
        state: str,
    ) -> str:
        if state not in self.TRANSITIONS.get(
            self.state,
            set(),
        ):
            raise RuntimeError(
                f"invalid transaction transition: "
                f"{self.state}->{state}"
            )

        self.state = state

        if state in (
            self.COMMITTED,
            self.ABORTED,
        ):
            self.completed_at = now_iso()

        return state

    def prepare(self) -> str:
        return self.transition(self.PREPARED)

    def start(self) -> str:
        return self.transition(self.EXECUTING)

    def verify(self) -> str:
        return self.transition(self.VERIFYING)

    def commit(self) -> str:
        return self.transition(self.COMMITTED)

    def abort(
        self,
        reason: str = "",
    ) -> str:
        self.abort_reason = reason
        return self.transition(self.ABORTED)

    def ready(self) -> bool:
        return bool(
            self.transaction_id
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "transaction_id": self.transaction_id,
            "state": self.state,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "abort_reason": self.abort_reason,
        }

__all__ = [
    "ModificationTransaction",
]
