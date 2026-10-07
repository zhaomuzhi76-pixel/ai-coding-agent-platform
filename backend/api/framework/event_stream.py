from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WSAgentEventStreamProtocol(Protocol):
    """
    API-facing event subscription port.

    The API stream depends only on subscription semantics.
    Event creation, dispatch and persistence remain below the API.
    """

    def subscribe(
        self,
        event_type: str,
        handler: object,
    ) -> None:
        ...

    def unsubscribe(
        self,
        event_type: str,
        handler: object,
    ) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "WSAgentEventStreamProtocol",
]
