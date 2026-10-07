from __future__ import annotations

from typing import Any

from backend.core.agent.agent_event import (
    AgentEvent,
)
from backend.core.events.contracts import (
    EventBusProtocol,
)


class MemoryWriteEmitter:
    """
    Memory write event emitter.

    Responsibility:
        - convert memory records into AgentEvent
        - publish memory_write events

    Not Responsible:
        - memory persistence
        - retrieval
        - embedding
        - event consumption
        - storage strategy
    """

    VERSION = "1.0"

    EVENT_TYPE = "memory_write"

    def __init__(
        self,
        event_bus: EventBusProtocol,
    ) -> None:
        if event_bus is None:
            raise ValueError(
                "event bus required"
            )

        if not isinstance(
            event_bus,
            EventBusProtocol,
        ):
            raise TypeError(
                "event_bus must implement EventBusProtocol"
            )

        self.event_bus = event_bus
        self.emit_count = 0

    async def emit(
        self,
        *,
        change: str,
        result: str,
        lesson: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Any]:

        event = AgentEvent(
            type=self.EVENT_TYPE,
            payload={
                "change": change,
                "result": result,
                "lesson": lesson,
                **(metadata or {}),
            },
            status="created",
        )

        response = await self.event_bus.publish(
            event
        )

        self.emit_count += 1

        return response

    def ready(
        self,
    ) -> bool:
        return self.event_bus.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "event_type": self.EVENT_TYPE,
            "emit_count": self.emit_count,
            "ready": self.ready(),
        }


__all__ = [
    "MemoryWriteEmitter",
]
