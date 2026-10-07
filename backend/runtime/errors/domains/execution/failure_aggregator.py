from __future__ import annotations

from backend.runtime.errors.domains.execution.failure_aggregation_contract import (
    RuntimeExecutionFailureAggregationProtocol,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)


class RuntimeExecutionFailureAggregator(
    RuntimeExecutionFailureAggregationProtocol,
):
    """
    Canonical Execution failure aggregation owner.

    Responsibility:
        - own aggregate failure semantics for node results
        - preserve canonical NodeExecutionResult values
        - expose failure count and failure presence

    Not Responsible:
        - exception classification
        - error normalization
        - execution
        - lifecycle mutation
        - scheduling
        - transport
        - persistence
    """

    VERSION = "1.0"

    def aggregate(
        self,
        results: list[NodeExecutionResult],
    ) -> list[NodeExecutionResult]:
        self._validate(results)

        return list(
            result
            for result in results
            if not result.success
        )

    def has_failures(
        self,
        results: list[NodeExecutionResult],
    ) -> bool:
        return bool(
            self.aggregate(results)
        )

    def failure_count(
        self,
        results: list[NodeExecutionResult],
    ) -> int:
        return len(
            self.aggregate(results)
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        results: list[NodeExecutionResult],
    ) -> None:
        if not isinstance(
            results,
            list,
        ):
            raise TypeError(
                "execution results must list"
            )

        for result in results:
            if not isinstance(
                result,
                NodeExecutionResult,
            ):
                raise TypeError(
                    "execution result must NodeExecutionResult"
                )


__all__ = [
    "RuntimeExecutionFailureAggregator",
]
