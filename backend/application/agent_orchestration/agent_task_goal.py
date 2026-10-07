from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTaskGoal:
    """
    Application task-goal contract.

    Owns:
        - stable task objective
        - workspace context
        - task metadata

    Does not own:
        - execution
        - planning
        - verification
        - completion decision
    """

    objective: str
    workspace: str = "."
    metadata: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.objective, str)
            or not self.objective.strip()
        ):
            raise ValueError(
                "task objective required"
            )

        if (
            not isinstance(self.workspace, str)
            or not self.workspace.strip()
        ):
            raise ValueError(
                "task workspace required"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata or {}),
        )

    def ready(self) -> bool:
        return bool(
            self.objective.strip()
            and self.workspace.strip()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "objective": self.objective,
            "workspace": self.workspace,
            "metadata": dict(self.metadata or {}),
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskGoal",
]
