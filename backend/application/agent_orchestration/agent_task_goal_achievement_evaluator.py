from __future__ import annotations

from backend.application.agent_orchestration.agent_task_goal import (
    AgentTaskGoal,
)
from backend.application.agent_orchestration.agent_task_objective_evidence import (
    AgentTaskObjectiveEvidence,
)
from backend.application.agent_orchestration.agent_task_goal_achievement_assessment import (
    AgentTaskGoalAchievementAssessment,
)


class AgentTaskGoalAchievementEvaluator:
    """
    Objective-achievement evaluator.

    Owns:
        - determine achievement from objective evidence

    Rules:
        - failed execution cannot achieve
        - failed verification cannot achieve
        - explicit continue/replan cannot achieve
        - explicit completion can achieve
        - concrete objective facts must all match
        - missing objective facts remain unproven

    Does not own:
        - execution
        - planning
        - decision policy
        - loop control
    """

    VERSION = "1.1"

    def evaluate(
        self,
        *,
        goal: AgentTaskGoal,
        evidence: AgentTaskObjectiveEvidence,
        execution_success: bool = True,
        verification_success: bool | None = None,
        orchestration_signal: str | None = None,
    ) -> AgentTaskGoalAchievementAssessment:
        self._validate(
            goal,
            evidence,
        )

        if not execution_success:
            return self._result(
                False,
                "execution failed",
            )

        if verification_success is False:
            return self._result(
                False,
                "verification failed",
            )

        signal = (
            orchestration_signal or ""
        ).strip().lower()

        if signal == "replan":
            return self._result(
                False,
                "task requires replanning",
            )

        if signal == "continue":
            return self._result(
                False,
                "task requires continued execution",
            )

        if signal == "completed":
            return self._result(
                True,
                "explicit completion evidence",
            )

        if evidence.complete:
            return self._result(
                True,
                "objective facts match",
            )

        return self._result(
            False,
            "objective achievement remains unproven",
        )

    @staticmethod
    def _result(
        achieved: bool,
        reason: str,
    ) -> AgentTaskGoalAchievementAssessment:
        return AgentTaskGoalAchievementAssessment(
            achieved=achieved,
            reason=reason,
        )

    @staticmethod
    def _validate(
        goal: AgentTaskGoal,
        evidence: AgentTaskObjectiveEvidence,
    ) -> None:
        if not isinstance(
            goal,
            AgentTaskGoal,
        ):
            raise TypeError(
                "task goal required"
            )

        if not isinstance(
            evidence,
            AgentTaskObjectiveEvidence,
        ):
            raise TypeError(
                "objective evidence required"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskGoalAchievementEvaluator",
]
