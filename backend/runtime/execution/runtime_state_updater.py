from __future__ import annotations

from collections.abc import Iterable

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)
from backend.runtime.execution.runtime_node_state import (
    RuntimeNodeState,
)


class RuntimeStateUpdater:
    """
    Runtime execution lifecycle commit boundary.

    Responsibility:
        - own runtime lifecycle state commits
        - promote executable nodes through READY to RUNNING
        - commit execution results into terminal states

    Not Responsible:
        - execute node
        - scheduling
        - node selection
        - retry policy
        - persistence
    """

    VERSION = "5.1"

    RESPONSIBILITY = (
        "runtime_node_lifecycle_commit",
    )

    def start(
        self,
        state: RuntimeExecutionState,
        node_ids: Iterable[str],
    ) -> None:
        if not isinstance(
            state,
            RuntimeExecutionState,
        ):
            raise TypeError(
                "state must RuntimeExecutionState"
            )

        if node_ids is None:
            raise ValueError(
                "node ids required"
            )

        for node_id in node_ids:
            if not isinstance(
                node_id,
                str,
            ) or not node_id.strip():
                raise ValueError(
                    "node id required"
                )

            runtime = state.get(
                node_id.strip()
            )

            if runtime is None:
                raise KeyError(
                    f"runtime node not found: {node_id}"
                )

            if runtime.state is RuntimeNodeState.CREATED:
                runtime.transition(
                    RuntimeNodeState.READY
                )

            if runtime.state is RuntimeNodeState.READY:
                runtime.transition(
                    RuntimeNodeState.RUNNING
                )

            elif runtime.state is not RuntimeNodeState.RUNNING:
                raise RuntimeError(
                    "runtime node cannot start from state: "
                    f"{runtime.state.value}"
                )

    def update(
        self,
        state: RuntimeExecutionState,
        results: list[NodeExecutionResult],
    ) -> None:
        if not isinstance(
            state,
            RuntimeExecutionState,
        ):
            raise TypeError(
                "state must RuntimeExecutionState"
            )

        if not isinstance(
            results,
            list,
        ):
            raise TypeError(
                "results must list"
            )

        for result in results:
            if not isinstance(
                result,
                NodeExecutionResult,
            ):
                raise TypeError(
                    "result must NodeExecutionResult"
                )

            runtime = state.get(
                result.node_id
            )

            if runtime is None:
                raise KeyError(
                    f"runtime node not found: {result.node_id}"
                )

            target = (
                RuntimeNodeState.SUCCESS
                if result.success
                else RuntimeNodeState.FAILED
            )

            runtime.transition(
                target
            )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": "RuntimeStateUpdater",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeStateUpdater",
]
