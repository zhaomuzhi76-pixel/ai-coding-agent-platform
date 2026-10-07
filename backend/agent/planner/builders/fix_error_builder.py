from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class FixErrorBuilder(BaseStepBuilder):
    """fix_error 意图 → fix_error step。"""

    VERSION = "1.0"
    RESPONSIBILITY = ("fix_error_plan_step_builder",)

    def build(self, context: dict[str, Any] | None = None) -> list[PlanStep]:
        context = context or {}
        raw_error = (context.get("raw_error")
                     or context.get("message")
                     or context.get("instruction")
                     or "")
        return [self._make_step(raw_error)]

    @staticmethod
    def _make_step(raw_error: str) -> PlanStep:
        return PlanStep.create(
            executor_type="fix_error",
            description="修复错误",
            parameters={"raw_error": raw_error,
                        "message": raw_error,
                        "instruction": raw_error},
        )

    def validate(self, steps: list[PlanStep]) -> bool:
        return bool(steps) and all(
            isinstance(s, PlanStep) and s.executor_type == "fix_error"
            for s in steps
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "responsibility": self.RESPONSIBILITY,
                "ready": self.ready()}


__all__ = ["FixErrorBuilder"]
