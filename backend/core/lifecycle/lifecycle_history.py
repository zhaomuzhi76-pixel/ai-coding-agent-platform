from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Final, TypedDict

from backend.core.contracts.value import (
    CoreValue,
)


_CST: Final = timezone(
    timedelta(hours=8)
)


class LifecycleHistoryItem(
    TypedDict,
):
    state: str
    timestamp: str


class LifecycleHistory:
    """
    Lifecycle history recorder.

    Responsibility:
        - record lifecycle states
        - expose lifecycle history snapshot

    Not Responsible:
        - lifecycle state machine
        - transition rules
        - execution
        - persistence
    """

    VERSION: Final = "2.0"

    RESPONSIBILITY: Final = (
        "lifecycle_history",
    )

    def __init__(
        self,
    ) -> None:
        self._items: list[
            LifecycleHistoryItem
        ] = []

    def record(
        self,
        state: str,
    ) -> None:
        if not isinstance(
            state,
            str,
        ):
            raise TypeError(
                "lifecycle state must be str"
            )

        if not state:
            raise ValueError(
                "lifecycle state required"
            )

        self._items.append(
            {
                "state": state,
                "timestamp": datetime.now(
                    _CST
                ).isoformat(),
            }
        )

    def snapshot(
        self,
    ) -> list[LifecycleHistoryItem]:
        return deepcopy(
            self._items
        )

    def count(
        self,
    ) -> int:
        return len(
            self._items
        )

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self._items,
                list,
            )
            and all(
                isinstance(
                    item,
                    dict,
                )
                and isinstance(
                    item.get("state"),
                    str,
                )
                and isinstance(
                    item.get("timestamp"),
                    str,
                )
                for item
                in self._items
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": "LifecycleHistory",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "count": self.count(),
            "history": [
                dict(item)
                for item
                in self._items
            ],
        }


__all__ = [
    "LifecycleHistory",
    "LifecycleHistoryItem",
]
