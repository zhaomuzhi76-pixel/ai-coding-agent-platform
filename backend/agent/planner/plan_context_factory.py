from __future__ import annotations

from typing import Any


class PlanContextFactory:
    VERSION = "1.1"

    RESPONSIBILITY = (
        "planner_context_factory"
    )

    def build(
        self,
        intent: Any,
        file_path: str | None = None,
        context: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> dict[str, Any]:

        builder_context = dict(
            context or {}
        )

        planner_intent = (
            intent.planner_intent
            if hasattr(
                intent,
                "planner_intent",
            )
            else intent
        )

        parameters = {}

        if hasattr(
            intent,
            "parameters",
        ):
            parameters.update(
                intent.parameters
            )

        path = (
            file_path
            or parameters.get(
                "path"
            )
            or parameters.get(
                "file_path"
            )
        )

        if path:
            parameters["path"] = path

        builder_context.update(
            {
                "intent":
                    planner_intent,

                "file_path":
                    path,

                "path":
                    path,

                "parameters":
                    parameters,

                "message":
                    message,
            }
        )

        return builder_context

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "PlanContextFactory",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "PlanContextFactory",
]
