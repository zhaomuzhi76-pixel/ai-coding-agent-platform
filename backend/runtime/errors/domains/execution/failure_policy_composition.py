from __future__ import annotations

from backend.runtime.errors.domains.execution.failure_aggregation_composition import (
    RuntimeExecutionFailureAggregationComposition,
)
from backend.runtime.errors.domains.execution.failure_aggregation_contract import (
    RuntimeExecutionFailureAggregationProtocol,
)
from backend.runtime.errors.domains.execution.failure_policy import (
    RuntimeExecutionFailurePolicy,
)
from backend.runtime.errors.domains.execution.failure_policy_contract import (
    RuntimeExecutionFailurePolicyProtocol,
)


class RuntimeExecutionFailurePolicyComposition:
    """
    Execution failure policy composition root.

    Responsibility:
        - assemble the canonical failure policy
        - provide the canonical aggregation dependency

    Not Responsible:
        - policy implementation semantics
        - failure aggregation implementation
        - execution
        - lifecycle
        - scheduling
        - transport
    """

    VERSION = "1.0"

    def __init__(
        self,
        aggregator: RuntimeExecutionFailureAggregationProtocol | None = None,
        policy: RuntimeExecutionFailurePolicyProtocol | None = None,
    ) -> None:
        self.aggregator = (
            aggregator
            if aggregator is not None
            else RuntimeExecutionFailureAggregationComposition().create()
        )

        if not isinstance(
            self.aggregator,
            RuntimeExecutionFailureAggregationProtocol,
        ):
            raise TypeError(
                "failure aggregation contract required"
            )

        self.policy = (
            policy
            if policy is not None
            else RuntimeExecutionFailurePolicy(
                self.aggregator
            )
        )

        if not isinstance(
            self.policy,
            RuntimeExecutionFailurePolicyProtocol,
        ):
            raise TypeError(
                "failure policy contract required"
            )

    def create(
        self,
    ) -> RuntimeExecutionFailurePolicyProtocol:
        if not self.ready():
            raise RuntimeError(
                "failure policy unavailable"
            )

        return self.policy

    def ready(
        self,
    ) -> bool:
        return (
            self.aggregator.ready()
            and self.policy.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "aggregator": self.aggregator.dump(),
            "policy": self.policy.dump(),
        }


__all__ = [
    "RuntimeExecutionFailurePolicyComposition",
]
