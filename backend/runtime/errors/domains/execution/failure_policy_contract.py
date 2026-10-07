from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)


class RuntimeExecutionFailureAction(StrEnum):
    """
    Canonical execution failure-policy action.

    Responsibility:
        - define stable failure-policy decision identity

    Not Responsible:
        - failure aggregation
        - exception normalization
        - execution
        - lifecycle mutation
        - scheduling
        - transport formatting
    """

    CONTINUE = "continue"
    STOP = "stop"


@runtime_checkable
class RuntimeExecutionFailurePolicyProtocol(Protocol):
    """
    Execution failure policy contract.

    Responsibility:
        - decide whether aggregated failures require stopping
        - preserve the supplied canonical failure results

    Not Responsible:
        - failure aggregation
        - exception classification
        - error normalization
        - execution
        - lifecycle mutation
        - scheduling
        - transport formatting
        - persistence
    """

    def decide(
        self,
        failures: list[NodeExecutionResult],
    ) -> RuntimeExecutionFailureAction:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "RuntimeExecutionFailureAction",
    "RuntimeExecutionFailurePolicyProtocol",
]
