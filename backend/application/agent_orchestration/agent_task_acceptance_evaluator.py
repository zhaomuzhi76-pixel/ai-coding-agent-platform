from __future__ import annotations

from backend.application.agent_orchestration.agent_task_acceptance_assessment import (
    AgentTaskAcceptanceAssessment,
)
from backend.application.agent_orchestration.agent_task_evidence import (
    AgentTaskEvidence,
)
from backend.application.agent_orchestration.agent_task_goal import (
    AgentTaskGoal,
)
from backend.application.agent_orchestration.agent_task_goal_achievement_evaluator import (
    AgentTaskGoalAchievementEvaluator,
)
from backend.application.agent_orchestration.agent_task_objective_evidence_adapter import (
    AgentTaskObjectiveEvidenceAdapter,
)


class AgentTaskAcceptanceEvaluator:
    """
    Application owner for goal acceptance.

    Owns:
        - project task evidence into objective evidence
        - convert goal-achievement facts into acceptance

    Does not own:
        - execution
        - verification execution
        - AgentDecision
        - loop control
    """

    VERSION = "1.2"

    def __init__(
        self,
        achievement_evaluator: AgentTaskGoalAchievementEvaluator
        | None = None,
        objective_evidence_adapter: AgentTaskObjectiveEvidenceAdapter
        | None = None,
    ) -> None:
        self.achievement_evaluator = (
            achievement_evaluator
            or AgentTaskGoalAchievementEvaluator()
        )
        self.objective_evidence_adapter = (
            objective_evidence_adapter
            or AgentTaskObjectiveEvidenceAdapter()
        )

    def evaluate(
        self,
        *,
        goal: AgentTaskGoal,
        evidence: AgentTaskEvidence,
    ) -> AgentTaskAcceptanceAssessment:
        self._validate(
            goal,
            evidence,
        )

        objective_evidence = (
            self.objective_evidence_adapter.adapt(
                goal=goal,
                evidence=evidence,
            )
        )

        achievement = (
            self.achievement_evaluator.evaluate(
                goal=goal,
                evidence=objective_evidence,
                execution_success=evidence.execution_success,
                verification_success=evidence.verification_success,
                orchestration_signal=evidence.orchestration_signal,
            )
        )

        return AgentTaskAcceptanceAssessment(
            accepted=achievement.achieved,
            reason=achievement.reason,
        )

    @staticmethod
    def _validate(
        goal: AgentTaskGoal,
        evidence: AgentTaskEvidence,
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
            AgentTaskEvidence,
        ):
            raise TypeError(
                "task evidence required"
            )

    def ready(self) -> bool:
        return (
            self.achievement_evaluator.ready()
            and self.objective_evidence_adapter.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "achievement_evaluator": (
                self.achievement_evaluator.dump()
            ),
            "objective_evidence_adapter": (
                self.objective_evidence_adapter.dump()
            ),
        }


__all__ = [
    "AgentTaskAcceptanceEvaluator",
]
