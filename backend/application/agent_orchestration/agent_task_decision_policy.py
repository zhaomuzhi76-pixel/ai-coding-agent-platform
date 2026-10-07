from __future__ import annotations

from backend.application.agent_orchestration.agent_task_completion_assessment import (
    AgentTaskCompletionAssessment,
)
from backend.core.agent.agent_decision import AgentDecision
from backend.core.agent.agent_orchestration_status import (
    AgentOrchestrationStatus,
)


class AgentTaskDecisionPolicy:
    """
    Application decision-policy boundary.

    Owns:
        - convert completion assessment to AgentDecision

    Does not own:
        - task completion evaluation
        - execution
        - planning
        - loop transitions
        - transport
        - persistence
    """

    VERSION = "1.1"

    def decide(
        self,
        *,
        assessment: AgentTaskCompletionAssessment,
        output_count: int,
        model: str | None,
    ) -> AgentDecision:
        if not isinstance(
            assessment,
            AgentTaskCompletionAssessment,
        ):
            raise TypeError(
                "completion assessment required"
            )

        if not isinstance(
            output_count,
            int,
        ) or output_count < 0:
            raise ValueError(
                "output_count must be >= 0"
            )

        if model is not None and not isinstance(
            model,
            str,
        ):
            raise TypeError(
                "model must str or None"
            )

        status = self._status(
            assessment
        )

        return AgentDecision(
            status=status,
            reason=assessment.reason,
            metadata={
                "output_count": output_count,
                "model": model,
            },
        )

    @staticmethod
    def _status(
        assessment: AgentTaskCompletionAssessment,
    ) -> AgentOrchestrationStatus:
        if assessment.requires_replan:
            return AgentOrchestrationStatus.REPLAN

        if assessment.can_continue:
            return AgentOrchestrationStatus.CONTINUE

        if assessment.completed:
            return AgentOrchestrationStatus.COMPLETED

        return AgentOrchestrationStatus.FAILED

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "assessment_driven": True,
        }


__all__ = [
    "AgentTaskDecisionPolicy",
]
