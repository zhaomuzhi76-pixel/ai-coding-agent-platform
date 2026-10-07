from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from backend.runtime.execution.runtime_node_runtime import (
    RuntimeNodeRuntime,
)


class RuntimeExecutionState:
    """
    Runtime execution state registry.

    Responsibility:
        - store runtime node states
        - provide runtime lookup
        - provide read-only node observation

    Not Responsible:
        - scheduling
        - execution
        - persistence
        - lifecycle transition
    """

    VERSION = "7.1"

    RESPONSIBILITY = (
        "runtime_execution_state_node_registry",
    )

    def __init__(
        self,
    ) -> None:
        self._nodes: dict[
            str,
            RuntimeNodeRuntime,
        ] = {}

    def register(
        self,
        runtime: RuntimeNodeRuntime,
    ) -> None:
        if not isinstance(
            runtime,
            RuntimeNodeRuntime,
        ):
            raise TypeError(
                "runtime must RuntimeNodeRuntime"
            )

        if runtime.node_id in self._nodes:
            raise ValueError(
                (
                    "duplicate runtime node: "
                    f"{runtime.node_id}"
                )
            )

        self._nodes[
            runtime.node_id
        ] = runtime

    def get(
        self,
        node_id: str,
    ) -> RuntimeNodeRuntime:
        runtime = self._nodes.get(
            node_id
        )

        if runtime is None:
            raise KeyError(
                node_id
            )

        return runtime

    def exists(
        self,
        node_id: str,
    ) -> bool:
        return node_id in self._nodes

    def contains(
        self,
        node_id: str,
    ) -> bool:
        return self.exists(node_id)

    def all(
        self,
    ) -> tuple[RuntimeNodeRuntime, ...]:
        return tuple(
            self._nodes.values()
        )

    def count(
        self,
    ) -> int:
        return len(
            self._nodes
        )

    def snapshot(
        self,
    ) -> Mapping[str, str]:
        snapshot: dict[str, str] = {
            runtime.node_id: runtime.state.value
            for runtime in self._nodes.values()
        }

        return MappingProxyType(
            snapshot
        )

    def ready(
        self,
    ) -> bool:
        return all(
            runtime.ready()
            for runtime in self._nodes.values()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "node_count": self.count(),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeExecutionState",
]
