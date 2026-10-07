from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTaskGoalAchievementAssessment:
    """
    Objective-level task achievement assessment.

    Owns:
        - whether the stated task objective is achieved
        - reason for the achievement judgment

    Does not own:
        - execution
        - verification
        - AgentDecision
        - loop control
    """

    achieved: bool
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.achieved,
            bool,
        ):
            raise TypeError(
                "achieved must bool"
            )

        if (
            not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise ValueError(
                "achievement reason required"
            )

    def ready(self) -> bool:
        return bool(self.reason.strip())

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "achieved": self.achieved,
            "reason": self.reason,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskGoalAchievementAssessment",
]
