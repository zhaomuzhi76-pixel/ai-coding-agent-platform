from __future__ import annotations

from backend.core.agent.agent_decision import AgentDecision
from backend.core.agent.agent_orchestration_loop_state import (
    AgentOrchestrationLoopState,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class AgentTaskOrchestrationLoopSupport:
    """
    Application support for autonomous task looping.
    """

    VERSION = "1.1"

    @staticmethod
    def validate(
        request: AgentRequest,
        session_id: str,
        max_iterations: int,
    ) -> None:
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

        if request.session_id.strip() != session_id.strip():
            raise ValueError(
                "request/session_id mismatch"
            )

        if not isinstance(
            max_iterations,
            int,
        ):
            raise TypeError(
                "max_iterations must int"
            )

        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be >= 1"
            )

    @staticmethod
    def initial(
        max_iterations: int,
    ) -> AgentOrchestrationLoopState:
        return AgentOrchestrationLoopState(
            iteration=0,
            max_iterations=max_iterations,
        )

    @staticmethod
    def require_decision(
        decision: AgentDecision | None,
    ) -> AgentDecision:
        if not isinstance(
            decision,
            AgentDecision,
        ):
            raise TypeError(
                "agent decision required"
            )
        return decision

    @staticmethod
    def require_result(
        result: ExecutionResult,
    ) -> ExecutionResult:
        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "execution result required"
            )
        return result

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskOrchestrationLoopSupport",
]
