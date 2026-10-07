from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)


class ExecutionStreamPayload(
    TypedDict,
):
    """
    Core-owned execution stream payload.
    """

    event: str
    data: CoreValue


@runtime_checkable
class ExecutionStreamProtocol(
    Protocol,
):
    """
    Core-owned execution stream boundary.

    Responsibility:
        - receive execution stream events

    Not Responsible:
        - stream scheduling
        - transport implementation
        - lifecycle management
        - result processing
    """

    async def emit(
        self,
        payload: ExecutionStreamPayload,
    ) -> None:
        ...


__all__ = [
    "ExecutionStreamPayload",
    "ExecutionStreamProtocol",
]
