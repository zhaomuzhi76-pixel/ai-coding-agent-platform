from __future__ import annotations

from backend.application.agent_service_contract import (
    AgentServiceProtocol,
)
from backend.application.agent_service_factory import (
    ApplicationAgentServiceFactory,
)
from backend.application.agent_orchestration.agent_task_orchestrator_factory import (
    AgentTaskOrchestratorFactory,
)
from backend.application.agent_orchestration.agent_task_orchestration_loop_factory import (
    AgentTaskOrchestrationLoopFactory,
)
from backend.application.runtime_execution_gateway.runtime_execution_gateway_contract import (
    ApplicationRuntimeExecutionGatewayContract,
)


class ApplicationAgentServiceAssembly:
    """
    Agent service assembly boundary.

    Owns:
        - agent service construction

    Does not own:
        - agent kernel construction
        - execution gateway construction
        - runtime lifecycle
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        execution_gateway: ApplicationRuntimeExecutionGatewayContract,
    ) -> AgentServiceProtocol:

        orchestrator = AgentTaskOrchestratorFactory().create(
            execution_gateway=execution_gateway,
        )

        loop = AgentTaskOrchestrationLoopFactory().create(
            orchestrator=orchestrator,
        )

        service = (
            ApplicationAgentServiceFactory()
            .create(
                orchestrator=loop,
            )
        )

        if not service.ready():
            raise RuntimeError(
                "agent service unavailable"
            )

        return service

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationAgentServiceAssembly",
]
