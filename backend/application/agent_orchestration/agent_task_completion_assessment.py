from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTaskCompletionAssessment:
    """
    Application task-completion assessment.

    Owns:
        - whether the task is complete
        - whether another iteration may continue
        - whether replanning is required

    Does not own:
        - execution
        - planning
        - decision construction
        - loop transition
    """

    completed: bool
    can_continue: bool
    requires_replan: bool
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.completed, bool):
            raise TypeError(
                "completed must bool"
            )

        if not isinstance(self.can_continue, bool):
            raise TypeError(
                "can_continue must bool"
            )

        if not isinstance(self.requires_replan, bool):
            raise TypeError(
                "requires_replan must bool"
            )

        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must str"
            )

        if self.completed and self.can_continue:
            raise ValueError(
                "completed task cannot continue"
            )

        if self.completed and self.requires_replan:
            raise ValueError(
                "completed task cannot require replan"
            )

    @property
    def terminal(self) -> bool:
        return self.completed

    def ready(self) -> bool:
        return bool(self.reason.strip())

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "completed": self.completed,
            "can_continue": self.can_continue,
            "requires_replan": self.requires_replan,
            "terminal": self.terminal,
            "reason": self.reason,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskCompletionAssessment",
]
