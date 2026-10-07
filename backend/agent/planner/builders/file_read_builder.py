from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class FileReadBuilder(
    BaseStepBuilder,
):
    VERSION = "1.1"

    RESPONSIBILITY = (
        "file_read_plan_step_builder"
    )

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        path = (
            context.get(
                "file_path"
            )
            or context.get(
                "path"
            )
            or ""
        )

        return [
            PlanStep.create(
                executor_type="file_read",
                description="读取文件内容",
                parameters={
                    "tool_call": {
                        "name":
                            "file_read",

                        "arguments": {
                            "path":
                                path,
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
            step.executor_type == "file_read"
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
                "FileReadBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "FileReadBuilder",
]
