from __future__ import annotations

from backend.application.agent_service_contract import (
    AgentServiceProtocol,
)
from backend.core.agent.agent_orchestration_protocol import (
    AgentOrchestrationProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class ApplicationAgentService(
    AgentServiceProtocol,
):
    """
    Application Agent execution facade.
    """

    VERSION = "4.1"

    RESPONSIBILITY = (
        "application_agent_execution_facade",
        "runtime_gateway_contract_delegation",
    )

    def __init__(
        self,
        orchestrator: AgentOrchestrationProtocol,
    ) -> None:
        if not isinstance(
            orchestrator,
            AgentOrchestrationProtocol,
        ):
            raise TypeError(
                "orchestrator must implement "
                "AgentOrchestrationProtocol"
            )

        self.orchestrator = orchestrator
        self.execution_count = 0

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        self._validate_request(
            request,
            session_id,
        )

        if not self.orchestrator.ready():
            raise RuntimeError(
                "runtime execution gateway not execution-ready"
            )

        result = await self.orchestrator.execute(
            request=request,
            session_id=session_id,
        )

        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "runtime gateway must return ExecutionResult"
            )

        self.execution_count += 1
        return result

    def ready(self) -> bool:
        return (
            isinstance(
                self.orchestrator,
                AgentOrchestrationProtocol,
            )
            and self.orchestrator.ready()
        )

    def execution_ready(self) -> bool:
        return self.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "execution_ready": self.execution_ready(),
            "execution_count": self.execution_count,
            "orchestrator": self.orchestrator.dump(),
        }

    @staticmethod
    def _validate_request(
        request: AgentRequest,
        session_id: str,
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


__all__ = [
    "ApplicationAgentService",
]
