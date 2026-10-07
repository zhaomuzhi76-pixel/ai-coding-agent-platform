from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class DeploymentBuilder(
    BaseStepBuilder,
):
    VERSION = "1.5"

    RESPONSIBILITY = (
        "deployment_plan_step_builder"
    )

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        command = (
            context.get(
                "command"
            )
            or context.get(
                "message"
            )
            or "docker compose up"
        )

        return [
            PlanStep.create(
                executor_type="deployment",
                description="执行部署",
                parameters={
                    "tool_call": {
                        "name":
                            "deployment",

                        "arguments": {
                            "command":
                                command,
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
            step.executor_type == "deployment"
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
                "DeploymentBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "DeploymentBuilder",
]
