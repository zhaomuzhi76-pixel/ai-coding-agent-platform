from __future__ import annotations

from typing import TypedDict


class SystemLifecycleSnapshot(
    TypedDict,
):
    """
    System lifecycle snapshot contract.

    Responsibility:

        - define system lifecycle state snapshot
    """

    state: str
    ready: bool
    started_at: str | None


__all__ = [
    "SystemLifecycleSnapshot",
]
