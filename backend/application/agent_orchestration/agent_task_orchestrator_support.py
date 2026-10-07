from __future__ import annotations

from backend.application.agent_orchestration.agent_task_completion_evaluator import (
    AgentTaskCompletionEvaluator,
)
from backend.application.agent_orchestration.agent_task_decision_policy import (
    AgentTaskDecisionPolicy,
)
from backend.core.agent.agent_decision import AgentDecision
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class AgentTaskOrchestratorSupport:
    """
    Application support for task-level Agent orchestration.

    Owns:
        - request validation
        - ExecutionResult -> AgentDecision delegation

    Does not own:
        - planning
        - runtime execution
        - result construction
    """

    VERSION = "1.1"

    def __init__(
        self,
        policy: AgentTaskDecisionPolicy | None = None,
        evaluator: AgentTaskCompletionEvaluator | None = None,
    ) -> None:
        self.policy = (
            policy
            or AgentTaskDecisionPolicy()
        )
        self.evaluator = (
            evaluator
            or AgentTaskCompletionEvaluator()
        )

    @staticmethod
    def validate_request(
        request: AgentRequest,
        session_id: str,
    ) -> AgentRequest:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must be AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "request not ready"
            )

        if (
            not isinstance(session_id, str)
            or not session_id.strip()
        ):
            raise ValueError(
                "session id required"
            )

        return request

    def decide(
        self,
        *,
        request: AgentRequest,
        result: ExecutionResult,
    ) -> AgentDecision:
        assessment = self.evaluator.evaluate(
            request=request,
            result=result,
        )

        return self.policy.decide(
            assessment=assessment,
            output_count=result.count(),
            model=result.model,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.policy.ready()
            and self.evaluator.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "policy": self.policy.dump(),
            "evaluator": self.evaluator.dump(),
        }


__all__ = [
    "AgentTaskOrchestratorSupport",
]
