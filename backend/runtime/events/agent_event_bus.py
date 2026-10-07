from __future__ import annotations

from collections.abc import Callable
import inspect
from typing import Any

from backend.core.agent.agent_event import AgentEvent
from backend.core.events.contracts import EventBusProtocol
from backend.runtime.events.agent_event_adapter import (
    RuntimeAgentEventAdapter,
)
from backend.runtime.events.event_bus import RuntimeEventBus


class RuntimeAgentEventBus(EventBusProtocol):
    """
    Core AgentEvent -> RuntimeEventBus bridge.

    Ownership:
        - RuntimeEventBus ownership belongs to runtime event plugin.
        - this class owns only the Core-facing bridge.
        - this class never constructs a RuntimeEventBus implicitly.

    Responsibility:
        - accept Core AgentEvent values
        - convert through RuntimeAgentEventAdapter
        - delegate dispatch to the injected RuntimeEventBus
        - preserve subscribe/unsubscribe symmetry

    Not Responsible:
        - RuntimeEventBus construction
        - event type definition
        - event persistence
        - transport delivery
        - business execution
    """

    VERSION = "1.2"

    def __init__(
        self,
        runtime_bus: RuntimeEventBus,
        adapter: RuntimeAgentEventAdapter | None = None,
    ) -> None:
        if runtime_bus is None:
            raise ValueError(
                "runtime event bus required"
            )

        if not isinstance(
            runtime_bus,
            RuntimeEventBus,
        ):
            raise TypeError(
                "runtime_bus must be RuntimeEventBus"
            )

        self.runtime_bus = runtime_bus

        self.adapter = (
            adapter
            if adapter is not None
            else RuntimeAgentEventAdapter()
        )

        if not self.adapter.ready():
            raise RuntimeError(
                "runtime agent event adapter not ready"
            )

        self._handlers: dict[
            tuple[str, int],
            Callable[..., Any],
        ] = {}

        self.publish_count = 0

    def subscribe(
        self,
        event_type: str,
        handler: Callable[..., Any],
    ) -> None:
        if not event_type:
            raise ValueError(
                "event type required"
            )

        if not callable(handler):
            raise TypeError(
                "event handler must callable"
            )

        key = (
            event_type,
            id(handler),
        )

        if key in self._handlers:
            return

        async def bridge_handler(
            runtime_event: Any,
        ) -> Any:
            result = handler(
                runtime_event
            )

            if inspect.isawaitable(result):
                return await result

            return result

        self._handlers[key] = bridge_handler

        self.runtime_bus.subscribe(
            event_type,
            bridge_handler,
        )

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[..., Any],
    ) -> None:
        if not event_type:
            raise ValueError(
                "event type required"
            )

        if not callable(handler):
            raise TypeError(
                "event handler must callable"
            )

        key = (
            event_type,
            id(handler),
        )

        bridge_handler = self._handlers.pop(
            key,
            None,
        )

        if bridge_handler is None:
            return

        self.runtime_bus.unsubscribe(
            event_type,
            bridge_handler,
        )

    async def publish(
        self,
        event: Any,
    ) -> list[Any]:
        if not isinstance(
            event,
            AgentEvent,
        ):
            raise TypeError(
                "AgentEvent required"
            )

        runtime_event = (
            self.adapter.to_runtime(
                event
            )
        )

        result = await self.runtime_bus.publish(
            runtime_event
        )

        self.publish_count += 1

        return result

    def clear_listeners(
        self,
    ) -> None:
        self._handlers.clear()
        self.runtime_bus.clear_listeners()

    def listener_count(
        self,
        event_type: str | None = None,
    ) -> int:
        return self.runtime_bus.listener_count(
            event_type
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.runtime_bus.ready()
            and self.adapter.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": (
                "runtime_agent_event_bus_bridge"
            ),
            "ready": self.ready(),
            "publish_count": self.publish_count,
            "listener_count": self.listener_count(),
            "runtime_bus": (
                self.runtime_bus.dump()
            ),
            "adapter": (
                self.adapter.dump()
            ),
        }


__all__ = [
    "RuntimeAgentEventBus",
]
