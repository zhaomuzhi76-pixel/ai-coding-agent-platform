from __future__ import annotations

from typing import Any

from backend.agent.planner.planner_engine import (
    PlannerEngine,
)

from backend.core.planning import (
    PlannerPortProtocol,
)

from backend.core.planning.contracts import (
    PlanningRequest,
    PlanningResult,
)


class _PlanningStepBridge:
    """
    Agent PlanStep to Core PlanningStepProtocol bridge.
    """

    def __init__(self, step) -> None:
        self.node_id = step.node_id
        self.executor_type = step.executor_type
        self.node_type = getattr(
            step,
            "node_type",
            "task",
        )
        self.description = step.description
        self.depends_on = list(
            step.depends_on
        )
        self.parameters = dict(
            step.parameters
        )
        self.metadata = dict(
            step.metadata
        )

    def ready(self) -> bool:
        return bool(
            self.node_id
            and self.executor_type
        )

    def dump(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "executor_type": self.executor_type,
            "node_type": self.node_type,
            "description": self.description,
            "depends_on": list(self.depends_on),
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }


class PlannerPortAdapter(
    PlannerPortProtocol,
):
    """
    Adapter between Agent PlannerEngine
    and Core PlannerPortProtocol.

    Responsibility:
        - expose core planner contract
        - validate the core request boundary
        - translate request/result boundary

    Does not own:
        - planning algorithm
        - plan construction
        - persistence
    """

    VERSION = "1.1"

    def __init__(
        self,
        engine: PlannerEngine,
    ) -> None:
        if not isinstance(engine, PlannerEngine):
            raise TypeError(
                "engine must be PlannerEngine"
            )

        if not engine.ready():
            raise RuntimeError(
                "planner engine unavailable"
            )

        self.engine = engine
        self.plan_count = 0

    async def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:
        self._validate_request(request)

        plan = await self.engine.create_plan(
            message=request.message,
            workspace=request.workspace,
            model=request.model,
        )

        self.plan_count += 1

        steps = tuple(
            _PlanningStepBridge(step)
            for step in plan.steps
        )

        result = PlanningResult(
            steps=steps,
            metadata={
                "plan_id": plan.plan_id,
                "goal": plan.goal,
                "workspace": plan.workspace,
                "model": plan.model,
            },
        )

        if not result.ready():
            raise RuntimeError(
                "planning result unavailable"
            )

        return result

    @staticmethod
    def _validate_request(
        request: PlanningRequest,
    ) -> None:
        if not isinstance(
            request,
            PlanningRequest,
        ):
            raise TypeError(
                "request must be PlanningRequest"
            )

        if not request.ready():
            raise ValueError(
                "planning request unavailable"
            )

    def ready(
        self,
    ) -> bool:
        return self.engine.ready()

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "engine": self.engine.dump(),
            "plan_count": self.plan_count,
        }


__all__ = [
    "PlannerPortAdapter",
]
