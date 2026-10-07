from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)


@runtime_checkable
class RuntimeExecutionFailureAggregationProtocol(
    Protocol,
):
    """
    Execution failure aggregation contract.

    Responsibility:
        - inspect a collection of node execution results
        - expose aggregate failure semantics
        - preserve original NodeExecutionResult instances

    Not Responsible:
        - node execution
        - exception normalization
        - lifecycle mutation
        - scheduling
        - transport formatting
        - persistence
    """

    def aggregate(
        self,
        results: list[NodeExecutionResult],
    ) -> list[NodeExecutionResult]:
        ...

    def has_failures(
        self,
        results: list[NodeExecutionResult],
    ) -> bool:
        ...

    def failure_count(
        self,
        results: list[NodeExecutionResult],
    ) -> int:
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
    "RuntimeExecutionFailureAggregationProtocol",
]
