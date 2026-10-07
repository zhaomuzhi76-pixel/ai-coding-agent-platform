from __future__ import annotations

from typing import Any

from backend.agent.planner.builder_registry import BuilderRegistry
from backend.agent.planner.plan_context_factory import PlanContextFactory
from backend.agent.planner.models.plan_step import PlanStep


class PlanBuilder:
    VERSION = "9.1"

    RESPONSIBILITY = (
        "planner_step_construction"
    )

    def __init__(
        self,
        builder_registry: BuilderRegistry,
        context_factory: PlanContextFactory | None = None,
    ) -> None:

        self.builder_registry = (
            builder_registry
        )

        self.context_factory = (
            context_factory
            or PlanContextFactory()
        )

    def build(
        self,
        intent: Any,
        file_path: str | None = None,
        context: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> list[PlanStep]:

        builder_context = (
            self.context_factory.build(
                intent=intent,
                file_path=file_path,
                context=context,
                message=message,
            )
        )

        builder_name = (
            self._resolve_builder(
                intent
            )
        )

        builder = (
            self.builder_registry.get(
                builder_name
            )
        )

        if builder is None:
            raise RuntimeError(
                f"Builder not found: {builder_name}"
            )

        steps = builder.build(
            builder_context
        )

        if not self.validate(
            steps
        ):
            raise RuntimeError(
                "invalid plan steps"
            )

        return steps

    def _resolve_builder(
        self,
        intent: Any,
    ) -> str:

        if hasattr(
            intent,
            "planner_intent",
        ):
            return str(
                intent.planner_intent
            )

        if hasattr(
            intent,
            "name",
        ):
            return str(
                intent.name
            )

        return str(
            intent
        )

    def validate(
        self,
        steps: list[PlanStep],
    ) -> bool:

        if not steps:
            return False

        return all(
            isinstance(
                step,
                PlanStep,
            )
            and step.ready()
            for step in steps
        )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.builder_registry
            and self.context_factory
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "PlanBuilder",
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "ready":
                self.ready(),
        }


__all__ = [
    "PlanBuilder",
]
