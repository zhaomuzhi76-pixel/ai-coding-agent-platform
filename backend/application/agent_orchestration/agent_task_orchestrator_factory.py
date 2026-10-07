from __future__ import annotations

from backend.application.agent_orchestration.agent_task_orchestrator import (
    AgentTaskOrchestrator,
)
from backend.application.agent_orchestration.agent_task_orchestrator_support import (
    AgentTaskOrchestratorSupport,
)
from backend.application.runtime_execution_gateway.runtime_execution_gateway_contract import (
    ApplicationRuntimeExecutionGatewayContract,
)


class AgentTaskOrchestratorFactory:
    """
    Sole construction owner for AgentTaskOrchestrator.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        execution_gateway: ApplicationRuntimeExecutionGatewayContract,
    ) -> AgentTaskOrchestrator:
        if not isinstance(
            execution_gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise TypeError(
                "execution gateway contract required"
            )

        orchestrator = AgentTaskOrchestrator(
            execution_gateway=execution_gateway,
            support=AgentTaskOrchestratorSupport(),
        )

        if not orchestrator.ready():
            raise RuntimeError(
                "agent task orchestrator unavailable"
            )

        return orchestrator

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskOrchestratorFactory",
]
