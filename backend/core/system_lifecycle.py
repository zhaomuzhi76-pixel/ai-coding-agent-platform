from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.system_lifecycle_contract import (
    SystemLifecycleSnapshot,
)

from backend.core.contracts.timestamp import now_timestamp


class SystemLifecycle:
    """
    System lifecycle state record.

    Responsibility:

        - record system bootstrap state
        - expose system readiness

    Not Responsible:

        - application lifecycle
        - service lifecycle
        - execution
        - resource cleanup
        - persistence
    """

    VERSION = "3.1"

    RESPONSIBILITY = (
        "system_lifecycle_state",
    )

    CREATED = "CREATED"
    READY = "READY"
    FAILED = "FAILED"

    STATES = frozenset(
        {
            CREATED,
            READY,
            FAILED,
        }
    )

    def __init__(
        self,
    ) -> None:

        self._state = self.CREATED
        self._started_at: str | None = None

    @property
    def state(
        self,
    ) -> str:

        return self._state

    @property
    def started_at(
        self,
    ) -> str | None:

        return self._started_at

    def mark_started(
        self,
    ) -> None:

        self._state = self.READY
        self._started_at = now_timestamp()

    def mark_failed(
        self,
    ) -> None:

        self._state = self.FAILED

    def ready(
        self,
    ) -> bool:

        return self._state == self.READY

    def status(
        self,
    ) -> SystemLifecycleSnapshot:

        return {
            "state": self._state,
            "ready": self.ready(),
            "started_at": self._started_at,
        }

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": "SystemLifecycle",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "status": self.status(),
        }


__all__ = [
    "SystemLifecycle",
]
