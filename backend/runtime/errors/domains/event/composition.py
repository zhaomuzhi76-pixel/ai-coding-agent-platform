from __future__ import annotations

from backend.runtime.errors.consumer_composition import (
    RuntimeErrorConsumerComposition,
)
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.domains.event.consumer import (
    RuntimeEventErrorConsumer,
)


class RuntimeEventErrorComposition:
    """
    Event-domain error consumer composition root.

    Responsibility:
        - assemble one Event-domain error consumer
        - provide the shared runtime error consumer dependency

    Not Responsible:
        - exception classification
        - normalization implementation
        - event dispatch
        - transport formatting
    """

    VERSION = "1.0"

    def __init__(
        self,
        consumer: RuntimeErrorConsumerProtocol | None = None,
    ) -> None:
        self.consumer = (
            consumer
            if consumer is not None
            else RuntimeErrorConsumerComposition().create()
        )

        if not isinstance(
            self.consumer,
            RuntimeErrorConsumerProtocol,
        ):
            raise TypeError(
                "runtime error consumer contract required"
            )

        self.event_consumer = RuntimeEventErrorConsumer(
            self.consumer
        )

    def create(
        self,
    ) -> RuntimeEventErrorConsumer:
        if not self.ready():
            raise RuntimeError(
                "event error consumer unavailable"
            )

        return self.event_consumer

    def ready(
        self,
    ) -> bool:
        return self.event_consumer.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "consumer": self.event_consumer.dump(),
        }


__all__ = [
    "RuntimeEventErrorComposition",
]
