from __future__ import annotations

from backend.runtime.errors.consumer_bridge import (
    RuntimeErrorConsumerBridge,
)
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.normalization_composition import (
    RuntimeErrorNormalizationComposition,
)


class RuntimeErrorConsumerComposition:
    """
    Runtime error consumption assembly boundary.

    Responsibility:
        - assemble the canonical Runtime error consumer
        - provide its normalization dependency

    Not Responsible:
        - exception classification
        - runtime execution
        - transport formatting
        - application business logic
    """

    VERSION = "1.0"

    def __init__(
        self,
        normalization: RuntimeErrorNormalizationComposition | None = None,
        consumer: RuntimeErrorConsumerProtocol | None = None,
    ) -> None:
        self.normalization = (
            normalization
            if normalization is not None
            else RuntimeErrorNormalizationComposition()
        )

        self.consumer = (
            consumer
            if consumer is not None
            else RuntimeErrorConsumerBridge(
                self.normalization.create()
            )
        )

        if not isinstance(
            self.consumer,
            RuntimeErrorConsumerProtocol,
        ):
            raise TypeError(
                "runtime error consumer contract required"
            )

    def create(
        self,
    ) -> RuntimeErrorConsumerProtocol:
        if not self.normalization.ready():
            raise RuntimeError(
                "runtime error normalization unavailable"
            )

        if not self.consumer.ready():
            raise RuntimeError(
                "runtime error consumer unavailable"
            )

        return self.consumer

    def ready(
        self,
    ) -> bool:
        return (
            self.normalization.ready()
            and self.consumer.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "normalization": (
                self.normalization.dump()
            ),
            "consumer": self.consumer.dump(),
        }


__all__ = [
    "RuntimeErrorConsumerComposition",
]
