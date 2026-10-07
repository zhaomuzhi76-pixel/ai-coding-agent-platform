from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class WorkspaceBuilder(
    BaseStepBuilder,
):
    VERSION = "1.1"

    RESPONSIBILITY = (
        "workspace_plan_step_builder"
    )

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        return [
            PlanStep.create(
                executor_type="workspace_scan",
                description="扫描工作区",
                parameters={
                    "tool_call": {
                        "name":
                            "workspace_scan",

                        "arguments": {},
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
            step.parameters.get(
                "tool_call",
                {},
            ).get(
                "name"
            )
            == "workspace_scan"
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
                "WorkspaceBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "WorkspaceBuilder",
]
