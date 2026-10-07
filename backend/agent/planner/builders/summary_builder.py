from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class SummaryBuilder(
    BaseStepBuilder,
):
    VERSION = "1.3"

    RESPONSIBILITY = (
        "summary_plan_step_builder"
    )

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        return [
            PlanStep.create(
                executor_type="summary",
                description="生成总结",
                parameters={
                    "tool_call": {
                        "name":
                            "summary",

                        "arguments": {
                            "content":
                                context.get(
                                    "content",
                                    "",
                                ),

                            "result":
                                context.get(
                                    "result",
                                    "",
                                ),
                        },
                    }
                },
                metadata={
                    "workflow_owner":
                        self.RESPONSIBILITY,
                },
            )
        ]

    def validate(
        self,
        steps: list[PlanStep],
    ) -> bool:

        if not steps:
            return False

        return all(
            step.executor_type == "summary"
            and "tool_call"
            in step.parameters
            for step in steps
        )

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "SummaryBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "SummaryBuilder",
]
