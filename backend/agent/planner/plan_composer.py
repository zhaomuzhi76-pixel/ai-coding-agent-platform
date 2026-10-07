from __future__ import annotations

from typing import List

from backend.agent.planner.models.plan_step import (
    PlanStep,
)


class PlanComposer:
    """
    Plan composition boundary.

    Responsibility:

        - compose existing plan steps
        - normalize step dependency relations

    Owns:

        - dependency linking rules for composed plan order

    Not Responsible:

        - intent detection
        - step creation
        - workflow selection
        - builder dispatch
        - execution
        - tool invocation
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "plan_composition"
    )

    def compose(
        self,
        steps: List[PlanStep],
        parallel: bool = False,
    ) -> List[PlanStep]:

        if not steps:
            return []

        if parallel:
            # 多文件独立修改：只 normalize，不加链式依赖
            for step in steps:
                self._normalize_dependencies(step)
            return steps

        previous = None

        for step in steps:

            self._normalize_dependencies(
                step
            )

            if previous is not None:

                self._append_dependency(
                    step,
                    previous.node_id,
                )

            previous = step

        return steps

    def _normalize_dependencies(
        self,
        step: PlanStep,
    ) -> None:

        if step.depends_on is None:
            step.depends_on = []

    def _append_dependency(
        self,
        step: PlanStep,
        dependency_id: str,
    ) -> None:

        if dependency_id not in step.depends_on:

            step.depends_on.append(
                dependency_id
            )

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "PlanComposer",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "capabilities": [
                "step_order_composition",
                "dependency_normalization",
            ],
        }


__all__ = [
    "PlanComposer",
]
