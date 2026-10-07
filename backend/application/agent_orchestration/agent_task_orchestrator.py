from __future__ import annotations

from backend.application.agent_orchestration.agent_task_orchestrator_support import (
    AgentTaskOrchestratorSupport,
)
from backend.application.runtime_execution_gateway.runtime_execution_gateway_contract import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.core.agent.agent_decision import AgentDecision
from backend.core.agent.agent_orchestration_protocol import (
    AgentOrchestrationProtocol,
)
from backend.core.agent.agent_orchestration_status import (
    AgentOrchestrationStatus,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class AgentTaskOrchestrator(AgentOrchestrationProtocol):
    """
    Application task-level Agent orchestration owner.
    """

    VERSION = "1.1"

    def __init__(
        self,
        *,
        execution_gateway: ApplicationRuntimeExecutionGatewayContract,
        support: AgentTaskOrchestratorSupport | None = None,
    ) -> None:
        if not isinstance(
            execution_gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise TypeError(
                "execution gateway contract required"
            )

        self.execution_gateway = execution_gateway
        self.support = (
            support
            or AgentTaskOrchestratorSupport()
        )
        self.execution_count = 0
        self.completed_count = 0
        self.failed_count = 0
        self.last_decision: AgentDecision | None = None

    async def execute(
        self,
        *,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        request = self.support.validate_request(
            request,
            session_id,
        )

        result = await self.execution_gateway.execute(
            request=request,
            session_id=session_id,
        )

        if not isinstance(result, ExecutionResult):
            raise TypeError(
                "execution gateway must return ExecutionResult"
            )

        decision = self.decide(
            request=request,
            result=result,
        )

        self.execution_count += 1
        self.last_decision = decision

        if (
            decision.status
            == AgentOrchestrationStatus.COMPLETED
        ):
            self.completed_count += 1
        elif (
            decision.status
            == AgentOrchestrationStatus.FAILED
        ):
            self.failed_count += 1

        return result

    def decide(
        self,
        *,
        request: AgentRequest,
        result: ExecutionResult,
    ) -> AgentDecision:
        return self.support.decide(
            request=request,
            result=result,
        )

    def terminate_for_iteration_limit(
        self,
    ) -> AgentDecision:
        decision = AgentDecision(
            status=AgentOrchestrationStatus.FAILED,
            reason="agent iteration limit reached",
            metadata={
                "iteration_limit_reached": True,
            },
        )

        self.last_decision = decision
        self.failed_count += 1
        return decision

    def ready(self) -> bool:
        return (
            self.execution_gateway.ready()
            and self.support.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "last_decision": (
                self.last_decision.dump()
                if self.last_decision is not None
                else None
            ),
            "execution_gateway": type(
                self.execution_gateway
            ).__name__,
            "support": self.support.dump(),
        }


__all__ = [
    "AgentTaskOrchestrator",
]
