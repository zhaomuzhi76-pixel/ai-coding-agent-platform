from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class TextGenerateBuilder(
    BaseStepBuilder,
):
    VERSION = "1.1"

    RESPONSIBILITY = (
        "text_generate_step_builder"
    )

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:

        context = context or {}

        message = (
            context.get(
                "message"
            )
            or context.get(
                "content"
            )
            or "execute text generation"
        )

        return [
            PlanStep.create(
                executor_type="llm",
                description="文本生成",
                parameters={
                    "tool_call": {
                        "name":
                            "llm",

                        "arguments": {
                            "message":
                                message,
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
            step.executor_type == "llm"
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
                "TextGenerateBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "TextGenerateBuilder",
]
