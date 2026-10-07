from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, TypeAlias, runtime_checkable

from backend.core.contracts.value import CoreValue


EventPayload: TypeAlias = dict[str, CoreValue]


@runtime_checkable
class EventProtocol(Protocol):
    type: str

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


EventHandler: TypeAlias = Callable[
    [EventProtocol],
    Awaitable[CoreValue] | CoreValue,
]


@runtime_checkable
class EventBusProtocol(
    Protocol,
):
    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        ...

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        ...

    async def publish(
        self,
        event: EventProtocol,
    ) -> list[CoreValue]:
        ...

    def ready(
        self,
    ) -> bool:
        ...


@runtime_checkable
class EventTypeRegistryProtocol(
    Protocol,
):
    @classmethod
    def all(
        cls,
    ) -> tuple[str, ...]:
        ...

    @classmethod
    def contains(
        cls,
        event_type: str,
    ) -> bool:
        ...

    @classmethod
    def ready(
        cls,
    ) -> bool:
        ...


__all__ = [
    "EventHandler",
    "EventPayload",
    "EventBusProtocol",
    "EventProtocol",
    "EventTypeRegistryProtocol",
]
