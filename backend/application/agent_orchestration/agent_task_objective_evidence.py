from __future__ import annotations

from dataclasses import dataclass, field

from backend.application.agent_orchestration.agent_task_objective_fact import (
    AgentTaskObjectiveFact,
)


@dataclass(frozen=True)
class AgentTaskObjectiveEvidence:
    """
    Objective-level evidence collection.

    Owns:
        - concrete objective facts
        - evidence completeness

    Does not own:
        - execution
        - planning
        - acceptance decision
        - orchestration decision
    """

    facts: tuple[AgentTaskObjectiveFact, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        normalized = tuple(self.facts)

        if not all(
            isinstance(
                item,
                AgentTaskObjectiveFact,
            )
            for item in normalized
        ):
            raise TypeError(
                "facts must AgentTaskObjectiveFact"
            )

        object.__setattr__(
            self,
            "facts",
            normalized,
        )

    @property
    def complete(self) -> bool:
        return bool(self.facts) and all(
            item.matched
            for item in self.facts
        )

    @property
    def proven(self) -> bool:
        return bool(self.facts)

    def ready(self) -> bool:
        return all(
            item.ready()
            for item in self.facts
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "fact_count": len(self.facts),
            "proven": self.proven,
            "complete": self.complete,
            "facts": [
                item.dump()
                for item in self.facts
            ],
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskObjectiveEvidence",
]
