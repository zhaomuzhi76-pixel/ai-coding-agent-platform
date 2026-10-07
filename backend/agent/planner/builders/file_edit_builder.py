from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class FileEditBuilder(BaseStepBuilder):
    VERSION = "4.0"

    RESPONSIBILITY = (
        "file_edit_plan_step_builder",
    )

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

        instruction = (
            context.get("message")
            or context.get("instruction")
            or ""
        )

        return [
            self._modify_step(
                path,
                instruction,
            )
        ]

    @staticmethod
    def _modify_step(
        path: str,
        instruction: str,
    ) -> PlanStep:
        return PlanStep.create(
            executor_type="code_modify",
            description="修改代码",
            parameters={
                "tool_call": {
                    "name": "code_modify",
                    "arguments": {
                        "path": path,
                        "instruction": instruction,
                        # content 由 CodeModifyExecutor 从磁盘读取
                        "content": "",
                    },
                },
            },
        )

    def validate(
        self,
        steps: list[PlanStep],
    ) -> bool:
        if len(steps) != 1:
            return False

        step = steps[0]
        if not isinstance(step, PlanStep):
            return False

        return (
            step.parameters.get("tool_call", {}).get("name")
            == "code_modify"
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "FileEditBuilder",
]
