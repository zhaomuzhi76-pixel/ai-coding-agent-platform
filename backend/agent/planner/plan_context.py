from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from backend.agent.planner.models.planner_intent import (
    PlannerIntent,
)


@dataclass
class PlanContext:
    """
    Planner normalized context.

    Responsibility:

        - carry planner input
        - carry planner metadata

    Not Responsible:

        - task analysis
        - plan generation
        - execution
        - tool invocation
    """

    VERSION = "2.0"

    intent: PlannerIntent

    workspace: str = "."

    model: str | None = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def ready(
        self,
    ) -> bool:

        return self.validate()

    def validate(
        self,
    ) -> bool:

        return (
            isinstance(
                self.intent,
                PlannerIntent,
            )
            and bool(
                self.workspace
            )
        )

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.metadata.get(
            key,
            default,
        )

    def dump(
        self,
    ) -> Dict[str, Any]:

        return {
            "name":
                "PlanContext",

            "version":
                self.VERSION,

            "responsibility":
                "planner_context",

            "ready":
                self.ready(),

            "intent":
                self.intent.dump(),

            "workspace":
                self.workspace,

            "model":
                self.model,

            "metadata":
                dict(
                    self.metadata
                ),
        }


__all__ = [
    "PlanContext",
]
