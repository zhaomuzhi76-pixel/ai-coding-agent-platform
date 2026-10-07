from __future__ import annotations

from backend.runtime.events.event_bus import RuntimeEventBus
from backend.runtime.events.node_event_producer import (
    RuntimeNodeEventProducer,
)
from backend.runtime.plugin.capability import RuntimeCapability


class NodeEventPlugin:
    """
    Runtime node event capability plugin.
    """

    VERSION = "1.0"

    name = "node_events"
    version = VERSION

    BUS_CAPABILITY = RuntimeCapability(
        category="events",
        name="bus",
        version=VERSION,
    )

    PRODUCER_CAPABILITY = RuntimeCapability(
        category="events",
        name="node_producer",
        version=VERSION,
    )

    def __init__(self) -> None:
        self.event_bus = RuntimeEventBus()
        self.producer = RuntimeNodeEventProducer(
            self.event_bus
        )

    def capabilities(
        self,
    ) -> list[RuntimeCapability]:
        return [
            self.BUS_CAPABILITY,
            self.PRODUCER_CAPABILITY,
        ]

    def register(
        self,
        registry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        registry.register(
            self.BUS_CAPABILITY,
            self.event_bus,
        )
        registry.register(
            self.PRODUCER_CAPABILITY,
            self.producer,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.event_bus.ready()
            and self.producer.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": tuple(
                capability.key()
                for capability in self.capabilities()
            ),
            "ready": self.ready(),
        }


__all__ = [
    "NodeEventPlugin",
]
