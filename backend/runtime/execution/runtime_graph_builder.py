from __future__ import annotations

from backend.runtime.contracts.runtime_execution_plan import (
    RuntimeExecutionPlan,
)
from backend.core.execution.runtime_execution_step import (
    RuntimeExecutionStep,
)
from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)
from backend.runtime.execution.runtime_graph_validator import (
    RuntimeGraphValidator,
)
from backend.core.execution import (
    RuntimeExecutionStep,
)


class RuntimeGraphBuilder:
    """
    Runtime execution plan builder.

    Responsibility:
        - create runtime graph topology
        - preserve execution step data
        - delegate graph validation
        - wrap graph into execution plan

    Not Responsible:
        - runtime state creation
        - scheduling
        - execution
        - lifecycle mutation
        - persistence
    """

    VERSION = "6.0"

    RESPONSIBILITY = (
        "runtime_execution_plan_building",
        "runtime_execution_step_mapping",
    )

    def __init__(
        self,
        validator: RuntimeGraphValidator | None = None,
    ) -> None:
        self.validator = (
            validator
            or RuntimeGraphValidator()
        )

    def build(
        self,
        steps: list[RuntimeExecutionStep],
    ) -> RuntimeExecutionPlan:
        if not isinstance(
            steps,
            list,
        ):
            raise TypeError(
                "steps must list"
            )

        graph = RuntimeGraph()

        for step in steps:
            if not isinstance(
                step,
                RuntimeExecutionStep,
            ):
                raise TypeError(
                    "invalid runtime execution step"
                )

            graph.add_node(
                RuntimeExecutionStep(
                    node_id=step.node_id,
                    executor_type=step.executor_type,
                    node_type=step.node_type,
                    description=step.description,
                    depends_on=list(
                        step.depends_on
                    ),
                    parameters=dict(
                        step.parameters
                    ),
                    metadata=dict(
                        step.metadata
                    ),
                )
            )

        self.validator.validate(
            graph
        )

        return RuntimeExecutionPlan(
            graph=graph,
        )

    def ready(
        self,
    ) -> bool:
        return self.validator.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "validator": self.validator.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeGraphBuilder",
]
