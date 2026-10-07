from __future__ import annotations

from backend.application.agent_orchestration.agent_task_acceptance_evaluator import (
    AgentTaskAcceptanceEvaluator,
)
from backend.application.agent_orchestration.agent_task_completion_assessment import (
    AgentTaskCompletionAssessment,
)
from backend.application.agent_orchestration.agent_task_evidence import (
    AgentTaskEvidence,
)
from backend.application.agent_orchestration.agent_task_evidence_adapter import (
    AgentTaskEvidenceAdapter,
)
from backend.application.agent_orchestration.agent_task_goal import (
    AgentTaskGoal,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class AgentTaskCompletionEvaluator:
    """
    Application owner for task completion evaluation.

    Owns:
        - create task goal
        - project execution evidence
        - evaluate goal acceptance
        - normalize completion assessment

    Does not own:
        - AgentDecision
        - execution
        - planning
        - loop transition
    """

    VERSION = "1.2"

    def __init__(
        self,
        evidence_adapter: AgentTaskEvidenceAdapter | None = None,
        acceptance_evaluator: AgentTaskAcceptanceEvaluator | None = None,
    ) -> None:
        self.evidence_adapter = (
            evidence_adapter
            or AgentTaskEvidenceAdapter()
        )
        self.acceptance_evaluator = (
            acceptance_evaluator
            or AgentTaskAcceptanceEvaluator()
        )

    def evaluate(
        self,
        *,
        request: AgentRequest,
        result: ExecutionResult,
    ) -> AgentTaskCompletionAssessment:
        self._validate(
            request,
            result,
        )

        goal = AgentTaskGoal(
            objective=request.message,
            workspace=request.workspace,
            metadata=dict(request.metadata),
        )

        evidence = self.evidence_adapter.adapt(
            result=result,
        )

        acceptance = (
            self.acceptance_evaluator.evaluate(
                goal=goal,
                evidence=evidence,
            )
        )

        return AgentTaskCompletionAssessment(
            completed=acceptance.accepted,
            can_continue=(
                not acceptance.accepted
                and evidence.execution_success
                and evidence.orchestration_signal
                not in ("replan",)
            ),
            requires_replan=(
                evidence.orchestration_signal
                == "replan"
            ),
            reason=acceptance.reason,
        )

    @staticmethod
    def _validate(
        request: AgentRequest,
        result: ExecutionResult,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must be AgentRequest"
            )

        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "result must be ExecutionResult"
            )

    def ready(self) -> bool:
        return (
            self.evidence_adapter.ready()
            and self.acceptance_evaluator.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "evidence_adapter": (
                self.evidence_adapter.dump()
            ),
            "acceptance_evaluator": (
                self.acceptance_evaluator.dump()
            ),
        }


__all__ = [
    "AgentTaskCompletionEvaluator",
]
