from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.plugins.intelligence.memory_adapter import (
    IntelligenceMemoryAdapter,
)
from backend.runtime.plugins.intelligence.memory_event_consumer import (
    IntelligenceMemoryEventConsumer,
)


@runtime_checkable
class RuntimeMemoryCapabilityProviderProtocol(
    Protocol,
):
    def create(self) -> IntelligenceMemoryAdapter:
        ...


class IntelligenceEventBinder:
    """
    Bind runtime intelligence event consumers.

    Responsibility:
        - resolve intelligence memory capability
        - subscribe memory consumers to runtime events
    """

    VERSION = "1.0"
    EVENT_TYPE = "memory_write"

    def __init__(
        self,
        *,
        capability_registry,
        event_bus,
    ) -> None:
        if capability_registry is None:
            raise ValueError(
                "capability registry required"
            )
        if event_bus is None:
            raise ValueError(
                "event bus required"
            )

        self.capability_registry = capability_registry
        self.event_bus = event_bus
        self.consumer = None
        self.bound = False

    def bind(self) -> None:
        provider = self.capability_registry.resolve(
            RuntimeCapability(
                category="intelligence",
                name="memory",
                version="1.0",
            )
        )

        if not isinstance(
            provider,
            RuntimeMemoryCapabilityProviderProtocol,
        ):
            raise TypeError(
                "memory capability provider contract required"
            )

        adapter = provider.create()

        if not isinstance(
            adapter,
            IntelligenceMemoryAdapter,
        ):
            raise TypeError(
                "memory capability result contract required"
            )

        self.consumer = IntelligenceMemoryEventConsumer(
            adapter
        )

        self.event_bus.subscribe(
            self.EVENT_TYPE,
            self.consumer.consume,
        )

        self.bound = True

    def ready(self) -> bool:
        return (
            self.bound
            and self.consumer is not None
            and self.consumer.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "event_type": self.EVENT_TYPE,
            "bound": self.bound,
            "consumer": (
                self.consumer.dump()
                if self.consumer is not None
                else None
            ),
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceEventBinder",
    "RuntimeMemoryCapabilityProviderProtocol",
]
