from __future__ import annotations

from backend.runtime.errors.domains.execution.failure_aggregation_contract import (
    RuntimeExecutionFailureAggregationProtocol,
)
from backend.runtime.errors.domains.execution.failure_aggregator import (
    RuntimeExecutionFailureAggregator,
)


class RuntimeExecutionFailureAggregationComposition:
    """
    Execution failure aggregation composition root.

    Responsibility:
        - assemble the canonical failure aggregator
        - expose the aggregation contract

    Not Responsible:
        - execution
        - normalization
        - lifecycle
        - scheduling
        - transport
    """

    VERSION = "1.0"

    def __init__(
        self,
        aggregator: (
            RuntimeExecutionFailureAggregationProtocol
            | None
        ) = None,
    ) -> None:
        self.aggregator = (
            aggregator
            if aggregator is not None
            else RuntimeExecutionFailureAggregator()
        )

        if not isinstance(
            self.aggregator,
            RuntimeExecutionFailureAggregationProtocol,
        ):
            raise TypeError(
                "failure aggregation contract required"
            )

    def create(
        self,
    ) -> RuntimeExecutionFailureAggregationProtocol:
        if not self.ready():
            raise RuntimeError(
                "failure aggregation unavailable"
            )

        return self.aggregator

    def ready(
        self,
    ) -> bool:
        return self.aggregator.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "aggregator": self.aggregator.dump(),
        }


__all__ = [
    "RuntimeExecutionFailureAggregationComposition",
]
