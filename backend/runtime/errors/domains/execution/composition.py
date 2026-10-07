from __future__ import annotations

from backend.runtime.errors.consumer_composition import (
    RuntimeErrorConsumerComposition,
)
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.domains.execution.consumer import (
    RuntimeExecutionErrorConsumer,
)


class RuntimeExecutionErrorComposition:
    """
    Execution-domain error consumer composition root.

    Responsibility:
        - assemble one Execution-domain error consumer
        - provide the shared runtime error consumer dependency
        - expose the canonical Execution error boundary

    Not Responsible:
        - exception classification
        - normalization implementation
        - runtime execution
        - scheduling
        - transport formatting
        - application policy
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

        self.execution_consumer = (
            RuntimeExecutionErrorConsumer(
                self.consumer
            )
        )

    def create(
        self,
    ) -> RuntimeExecutionErrorConsumer:
        if not self.ready():
            raise RuntimeError(
                "execution error consumer unavailable"
            )

        return self.execution_consumer

    def ready(
        self,
    ) -> bool:
        return self.execution_consumer.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "domain": self.execution_consumer.DOMAIN.value,
            "ready": self.ready(),
            "consumer": self.execution_consumer.dump(),
        }


__all__ = [
    "RuntimeExecutionErrorComposition",
]
