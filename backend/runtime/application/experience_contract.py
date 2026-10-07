from __future__ import annotations

from typing import Protocol


class RuntimeExperienceListenerProtocol(
    Protocol,
):
    """
    Runtime experience listener contract.

    Responsibility:
        - receive runtime completion events
        - receive runtime failure events

    Not Responsible:
        - event subscription
        - event creation
        - runtime execution
        - persistence
    """

    async def on_runtime_completed(
        self,
        data: dict[str, object],
    ) -> object:
        ...

    async def on_runtime_failed(
        self,
        data: dict[str, object],
    ) -> object:
        ...


__all__ = [
    "RuntimeExperienceListenerProtocol",
]
