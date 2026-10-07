from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class AnalysisBuilder(
    BaseStepBuilder,
):
    VERSION = "2.1"

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        arguments = {
            "content": context.get(
                "content",
                "",
            ),
            "path": (
                context.get(
                    "file_path"
                )
                or context.get(
                    "path",
                    "",
                )
            ),
        }

        return [
            PlanStep.create(
                executor_type="code_analysis",
                description="分析代码",
                parameters={
                    "tool_call": {
                        "name": "code_analysis",
                        "arguments": arguments,
                    }
                },
            )
        ]

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "AnalysisBuilder",
            "version":
                self.VERSION,
            "ready":
                self.ready(),
        }


__all__ = [
    "AnalysisBuilder",
]
