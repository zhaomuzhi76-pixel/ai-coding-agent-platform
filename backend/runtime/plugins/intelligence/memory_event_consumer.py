from __future__ import annotations

from backend.runtime.events.event import RuntimeEvent
from backend.runtime.plugins.intelligence.memory_record import (
    RuntimeEngineeringMemoryRecord,
)


class IntelligenceMemoryEventConsumer:
    """Runtime memory event consumer."""

    VERSION = "2.0"
    EVENT_TYPE = "memory_write"

    def __init__(
        self,
        memory_adapter,
    ) -> None:
        if memory_adapter is None:
            raise ValueError(
                "memory adapter required"
            )
        self.memory_adapter = memory_adapter
        self.consume_count = 0

    async def consume(
        self,
        event: RuntimeEvent,
    ) -> None:
        if not isinstance(
            event,
            RuntimeEvent,
        ):
            raise TypeError(
                "event must RuntimeEvent"
            )

        if event.type != self.EVENT_TYPE:
            raise ValueError(
                "unsupported event type"
            )

        payload = dict(event.data)

        record = RuntimeEngineeringMemoryRecord(
            change=str(payload.get("change", "")),
            result=str(payload.get("result", "")),
            lesson=str(payload.get("lesson", "")),
        )

        if not record.ready():
            return

        self.memory_adapter.remember(record)
        self.consume_count += 1

    def ready(self) -> bool:
        return self.memory_adapter.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "event_type": self.EVENT_TYPE,
            "consume_count": self.consume_count,
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceMemoryEventConsumer",
]
