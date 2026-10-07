from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class CodeModifyBuilder(
    BaseStepBuilder,
):
    VERSION = "2.1"

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        path = (
            context.get("file_path")
            or context.get("path")
            or ""
        )

        instruction = context.get(
            "message",
            "",
        )

        return [
            PlanStep.create(
                executor_type="code_modify",
                description="修改代码",
                parameters={
                    "tool_call": {
                        "name": "code_modify",
                        "arguments": {
                            "path": path,
                            "instruction": instruction,
                            "content": context.get(
                                "content",
                                "",
                            ),
                        },
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
                "CodeModifyBuilder",
            "version":
                self.VERSION,
            "ready":
                self.ready(),
        }


__all__ = [
    "CodeModifyBuilder",
]
