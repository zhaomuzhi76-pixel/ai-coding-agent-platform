from __future__ import annotations

from backend.runtime.contracts.execution import (
    RuntimeExecutionPlan,
)


class RuntimeExecutionPlanGuard:
    """
    Runtime execution plan guard.

    Responsibility:
        - verify execution plan boundary

    Not Responsible:
        - build plan
        - execute plan
        - mutate graph
    """

    VERSION = "1.1"

    def validate(
        self,
        plan,
    ) -> RuntimeExecutionPlan:
        if not isinstance(
            plan,
            RuntimeExecutionPlan,
        ):
            raise TypeError(
                "invalid runtime execution plan"
            )

        return plan

    def ready(
        self,
    ) -> bool:
        return True


__all__ = [
    "RuntimeExecutionPlanGuard",
]
