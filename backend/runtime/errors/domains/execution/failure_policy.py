from __future__ import annotations

from backend.runtime.errors.domains.execution.failure_aggregation_contract import (
    RuntimeExecutionFailureAggregationProtocol,
)
from backend.runtime.errors.domains.execution.failure_policy_contract import (
    RuntimeExecutionFailureAction,
    RuntimeExecutionFailurePolicyProtocol,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)


class RuntimeExecutionFailurePolicy(
    RuntimeExecutionFailurePolicyProtocol,
):
    """
    Canonical Execution failure policy owner.

    Responsibility:
        - decide the action for aggregated execution failures
        - preserve current non-fail-fast execution semantics

    Not Responsible:
        - failure aggregation
        - exception classification
        - error normalization
        - node execution
        - lifecycle mutation
        - scheduling
        - transport
    """

    VERSION = "1.0"

    def __init__(
        self,
        aggregator: RuntimeExecutionFailureAggregationProtocol | None = None,
    ) -> None:
        self.aggregator = aggregator

        if aggregator is not None and not isinstance(
            aggregator,
            RuntimeExecutionFailureAggregationProtocol,
        ):
            raise TypeError(
                "failure aggregation contract required"
            )

        self.decision_count = 0
        self.continue_count = 0
        self.stop_count = 0
        self.last_action: RuntimeExecutionFailureAction | None = None

    def decide(
        self,
        failures: list[NodeExecutionResult],
    ) -> RuntimeExecutionFailureAction:
        self._validate(failures)

        if self.aggregator is not None:
            expected = self.aggregator.aggregate(
                failures
            )
            if len(expected) != len(failures):
                raise ValueError(
                    "failure policy requires aggregated failures"
                )

        action = RuntimeExecutionFailureAction.CONTINUE

        self.decision_count += 1
        self.continue_count += 1
        self.last_action = action

        return action

    def ready(
        self,
    ) -> bool:
        return (
            self.aggregator is None
            or self.aggregator.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "decision_count": self.decision_count,
            "continue_count": self.continue_count,
            "stop_count": self.stop_count,
            "last_action": (
                self.last_action.value
                if self.last_action is not None
                else None
            ),
            "aggregator": (
                self.aggregator.dump()
                if self.aggregator is not None
                else None
            ),
        }

    @staticmethod
    def _validate(
        failures: list[NodeExecutionResult],
    ) -> None:
        if not isinstance(
            failures,
            list,
        ):
            raise TypeError(
                "execution failures must list"
            )

        for result in failures:
            if not isinstance(
                result,
                NodeExecutionResult,
            ):
                raise TypeError(
                    "execution failure must NodeExecutionResult"
                )

            if result.success:
                raise ValueError(
                    "failure policy received successful result"
                )


__all__ = [
    "RuntimeExecutionFailurePolicy",
]
