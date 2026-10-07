from __future__ import annotations

import inspect

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.events.contracts import (
    EventBusProtocol,
    EventHandler,
    EventProtocol,
)

from backend.core.events.event import (
    CoreEvent,
)

from backend.core.events.subscription import (
    EventSubscription,
)

from backend.core.events.types import (
    CoreEventType,
)


class EventBus(
    EventBusProtocol,
):
    """
    In-memory core event bus.

    Owns:
        - subscription registry
        - handler dispatch
        - publish execution

    Does not own:
        - persistence
        - queue
        - retry
        - transport
        - business execution
    """

    VERSION = "1.1"

    def __init__(
        self,
    ) -> None:
        self._subscriptions: dict[
            str,
            list[EventSubscription],
        ] = {}

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:

        if not CoreEventType.contains(
            event_type,
        ):
            raise ValueError(
                f"unsupported event type: {event_type}"
            )

        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
        )

        self._subscriptions.setdefault(
            event_type,
            [],
        ).append(
            subscription
        )

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:

        subscriptions = (
            self._subscriptions.get(
                event_type,
                [],
            )
        )

        self._subscriptions[event_type] = [
            item
            for item in subscriptions
            if item.handler is not handler
        ]

    async def publish(
        self,
        event: EventProtocol,
    ) -> list[CoreValue]:

        if not isinstance(
            event,
            CoreEvent,
        ):
            raise TypeError(
                "event must CoreEvent"
            )

        results: list[CoreValue] = []

        for subscription in (
            self._subscriptions.get(
                event.type,
                [],
            )
        ):

            result = subscription.handler(
                event
            )

            if inspect.isawaitable(
                result,
            ):
                result = await result

            results.append(
                result
            )

        return results

    def ready(
        self,
    ) -> bool:

        return isinstance(
            self._subscriptions,
            dict,
        )

    def count(
        self,
    ) -> int:

        return sum(
            len(items)
            for items
            in self._subscriptions.values()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "subscription_count": self.count(),
            "event_types": tuple(
                self._subscriptions
            ),
            "ready": self.ready(),
        }


__all__ = [
    "EventBus",
]
