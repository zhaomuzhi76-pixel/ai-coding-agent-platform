from __future__ import annotations

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)


class DAGRoundResultValidator:
    """
    DAG round result contract validator.

    Responsibility:
        - validate round result entities
        - reject duplicate node results

    Not Responsible:
        - graph topology validation
        - execution
        - scheduling
        - state mutation
        - persistence
    """

    VERSION = "2.0"

    def validate(
        self,
        results: list[NodeExecutionResult],
    ) -> list[NodeExecutionResult]:
        if not isinstance(
            results,
            list,
        ):
            raise TypeError(
                "results must list"
            )

        seen: set[str] = set()

        for result in results:
            if not isinstance(
                result,
                NodeExecutionResult,
            ):
                raise TypeError(
                    "invalid node execution result"
                )

            node_id = result.node_id.strip()

            if not node_id:
                raise ValueError(
                    "result node_id required"
                )

            if node_id in seen:
                raise ValueError(
                    f"duplicate result node_id: {node_id}"
                )

            seen.add(node_id)

        return results

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


__all__ = [
    "DAGRoundResultValidator",
]
