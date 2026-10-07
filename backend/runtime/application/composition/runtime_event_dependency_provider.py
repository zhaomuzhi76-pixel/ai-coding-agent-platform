from __future__ import annotations


from backend.runtime.events.event_bus import (
    RuntimeEventBus,
)

from backend.runtime.plugins.intelligence.memory_emitter import (
    MemoryWriteEmitter,
)


class RuntimeEventDependencyProvider:
    """
    Runtime event dependency boundary.

    Responsibility:
        - resolve runtime event dependency
        - create memory event emitter

    Not Responsible:
        - event dispatch
        - memory persistence
        - processor execution
    """

    VERSION = "1.0"


    def __init__(
        self,
        event_bus: RuntimeEventBus,
    ) -> None:

        if event_bus is None:
            raise ValueError(
                "runtime event bus required"
            )

        self.event_bus = event_bus



    def create_memory_emitter(
        self,
    ) -> MemoryWriteEmitter:

        emitter = MemoryWriteEmitter(
            self.event_bus
        )

        if not emitter.ready():
            raise RuntimeError(
                "memory emitter unavailable"
            )

        return emitter



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
            "event_bus": (
                type(self.event_bus).__name__
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeEventDependencyProvider",
]
