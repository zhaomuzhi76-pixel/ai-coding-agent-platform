from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


class ProjectAnalysisBuilder(BaseStepBuilder):
    """
    Build a project_analysis step (single node).
    """

    VERSION = "1.0"
    RESPONSIBILITY = ("project_analysis_plan_step_builder",)

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:
        context = context or {}
        instruction = (
            context.get("message")
            or context.get("instruction")
            or "分析这个项目"
        )
        return [self._make_step(instruction)]

    @staticmethod
    def _make_step(instruction: str) -> PlanStep:
        return PlanStep.create(
            executor_type="project_analysis",
            description="项目分析",
            parameters={
                "message": instruction,
                "instruction": instruction,
            },
        )

    def validate(self, steps: list[PlanStep]) -> bool:
        if not steps:
            return False
        return all(
            isinstance(s, PlanStep)
            and s.executor_type == "project_analysis"
            for s in steps
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["ProjectAnalysisBuilder"]
