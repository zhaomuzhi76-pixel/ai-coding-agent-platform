from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from backend.core.errors import CoreErrorDetail
from backend.core.events.contracts import EventBusProtocol
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.domains.event.composition import (
    RuntimeEventErrorComposition,
)
from backend.runtime.events.event import RuntimeEvent


EventHandler = Callable[
    [RuntimeEvent],
    Awaitable[Any] | Any,
]


class RuntimeEventBus(EventBusProtocol):
    """
    Runtime event dispatch boundary.

    Responsibility:
        - subscribe handlers
        - publish runtime events
        - normalize handler failures through Event error consumer

    Not Responsible:
        - event entity ownership
        - event persistence
        - transport delivery
        - error classification
        - error normalization implementation
    """

    VERSION = "16.1"

    RESPONSIBILITY = (
        "runtime_event_dispatch_boundary",
    )

    def __init__(
        self,
        error_consumer: RuntimeErrorConsumerProtocol | None = None,
    ) -> None:
        self.listeners: dict[
            str,
            list[EventHandler],
        ] = {}

        self.publish_count = 0
        self.handler_success_count = 0
        self.handler_failure_count = 0
        self.last_error: CoreErrorDetail | None = None

        self.error_consumer = (
            error_consumer
            if error_consumer is not None
            else RuntimeEventErrorComposition().create()
        )

        if not isinstance(
            self.error_consumer,
            RuntimeErrorConsumerProtocol,
        ):
            raise TypeError(
                "runtime error consumer contract required"
            )

        if not self.error_consumer.ready():
            raise RuntimeError(
                "runtime event error consumer not ready"
            )

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        if not event_type:
            raise ValueError(
                "event type required"
            )

        if not callable(handler):
            raise TypeError(
                "event handler must callable"
            )

        handlers = self.listeners.setdefault(
            event_type,
            [],
        )

        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        handlers = self.listeners.get(
            event_type,
            [],
        )

        if handler in handlers:
            handlers.remove(handler)

        if not handlers:
            self.listeners.pop(
                event_type,
                None,
            )

    async def publish(
        self,
        event: RuntimeEvent,
    ) -> list[Any]:
        if not isinstance(
            event,
            RuntimeEvent,
        ):
            raise TypeError(
                "core RuntimeEvent required"
            )

        if not event.ready():
            raise ValueError(
                "runtime event not ready"
            )

        self.publish_count += 1

        results: list[Any] = []

        handlers = list(
            self.listeners.get(
                event.type,
                [],
            )
        )

        for handler in handlers:
            try:
                result = handler(event)

                if inspect.isawaitable(result):
                    result = await result

                results.append(result)
                self.handler_success_count += 1
                self.last_error = None

            except Exception as error:
                self.handler_failure_count += 1
                self.last_error = self.error_consumer.consume(
                    error,
                    operation="event.publish",
                    metadata={
                        "event_type": event.type,
                    },
                )
                results.append(None)

        return results

    def clear_listeners(self) -> None:
        self.listeners.clear()

    def listener_count(
        self,
        event_type: str | None = None,
    ) -> int:
        if event_type:
            return len(
                self.listeners.get(
                    event_type,
                    [],
                )
            )

        return sum(
            len(items)
            for items in self.listeners.values()
        )

    def ready(self) -> bool:
        return (
            self.error_consumer is not None
            and self.error_consumer.ready()
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": "RuntimeEventBus",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "listener_count": self.listener_count(),
            "publish_count": self.publish_count,
            "handler_success_count": (
                self.handler_success_count
            ),
            "handler_failure_count": (
                self.handler_failure_count
            ),
            "last_error": (
                self.last_error.dump()
                if self.last_error is not None
                else None
            ),
            "error_consumer": (
                self.error_consumer.dump()
            ),
        }


__all__ = [
    "RuntimeEventBus",
]
