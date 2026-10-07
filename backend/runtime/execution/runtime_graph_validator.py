from __future__ import annotations

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)
from backend.runtime.execution.runtime_graph_dependency_validator import (
    RuntimeGraphDependencyValidator,
)
from backend.runtime.execution.runtime_graph_cycle_validator import (
    RuntimeGraphCycleValidator,
)


class RuntimeGraphValidator:
    """
    Runtime graph validation facade.

    Responsibility:
        - enforce graph structural validity
        - coordinate dependency validation
        - coordinate cycle validation

    Not Responsible:
        - graph construction
        - dependency validation algorithm
        - cycle detection algorithm
        - topology calculation
        - execution
        - scheduling
    """

    VERSION = "2.1"

    RESPONSIBILITY = (
        "runtime_graph_validation_facade",
    )

    def __init__(
        self,
        *,
        dependency_validator=None,
        cycle_validator=None,
    ) -> None:
        self.dependency_validator = (
            dependency_validator
            if dependency_validator is not None
            else RuntimeGraphDependencyValidator()
        )

        self.cycle_validator = (
            cycle_validator
            if cycle_validator is not None
            else RuntimeGraphCycleValidator()
        )

    def validate(
        self,
        graph: RuntimeGraph,
    ) -> bool:
        if not isinstance(
            graph,
            RuntimeGraph,
        ):
            raise TypeError(
                "graph must RuntimeGraph"
            )

        if graph.node_count() == 0:
            raise ValueError(
                "runtime graph must contain at least one node"
            )

        if not self.dependency_validator.ready():
            raise RuntimeError(
                "graph dependency validator not ready"
            )

        if not self.cycle_validator.ready():
            raise RuntimeError(
                "graph cycle validator not ready"
            )

        self.dependency_validator.validate(
            graph
        )

        self.cycle_validator.validate(
            graph
        )

        return True

    def ready(
        self,
    ) -> bool:
        return (
            self.dependency_validator.ready()
            and self.cycle_validator.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": "RuntimeGraphValidator",
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeGraphValidator",
]
