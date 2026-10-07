from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTaskAcceptanceAssessment:
    """
    Application task-acceptance assessment.

    Owns:
        - whether goal acceptance is established
        - reason for acceptance outcome

    Does not own:
        - execution
        - planning
        - AgentDecision
        - loop transition
    """

    accepted: bool
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.accepted,
            bool,
        ):
            raise TypeError(
                "accepted must bool"
            )

        if not isinstance(
            self.reason,
            str,
        ) or not self.reason.strip():
            raise ValueError(
                "acceptance reason required"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "accepted": self.accepted,
            "reason": self.reason,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskAcceptanceAssessment",
]
