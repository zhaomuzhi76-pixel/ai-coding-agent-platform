from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import (
    BaseStepBuilder,
)

from backend.agent.planner.models.plan_step import (
    PlanStep,
)


class TestingBuilder(
    BaseStepBuilder,
):
    VERSION = "1.5"

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        file_path = (
            context.get(
                "file_path"
            )
            if context
            else None
        )

        return [
            self._build_test_step(
                file_path
            )
        ]

    def _build_test_step(
        self,
        file_path: str | None,
    ) -> PlanStep:

        command = (
            f"python -m compileall {file_path}"
            if file_path
            else "python -m compileall backend"
        )

        return PlanStep.create(
            executor_type="terminal",
            description="执行测试",
            parameters={
                "tool_call": {
                    "name": "terminal",
                    "arguments": {
                        "command": command,
                    },
                }
            },
        )


__all__ = [
    "TestingBuilder",
]
