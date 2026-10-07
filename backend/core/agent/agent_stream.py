from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, TypedDict, runtime_checkable

from backend.core.contracts.value import CoreValue


class AgentStreamPayload(TypedDict):
    """
    Core-owned agent stream payload contract.

    Responsibility:
        - define stable agent stream event payload
        - provide event name and output data

    Not Responsible:
        - stream scheduling
        - execution lifecycle
        - persistence
        - transport
    """

    event: str
    data: CoreValue


@runtime_checkable
class AgentStreamProtocol(
    Protocol,
):
    """
    Core-owned agent stream capability contract.

    Responsibility:
        - receive agent stream events

    Not Responsible:
        - stream execution
        - scheduling
        - result processing
        - transport implementation
    """

    async def emit(
        self,
        payload: AgentStreamPayload,
    ) -> None:
        ...


AgentStreamCallback = Callable[
    [
        AgentStreamPayload,
    ],
    Awaitable[None],
]


__all__ = [
    "AgentStreamPayload",
    "AgentStreamProtocol",
    "AgentStreamCallback",
]
