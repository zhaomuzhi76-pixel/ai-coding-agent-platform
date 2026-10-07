from __future__ import annotations

from backend.application.agent_service import (
    ApplicationAgentService,
)
from backend.application.agent_service_contract import (
    AgentServiceProtocol,
)
from backend.core.agent.agent_orchestration_protocol import (
    AgentOrchestrationProtocol,
)


class ApplicationAgentServiceFactory:
    """
    Sole construction owner for ApplicationAgentService.

    Owns:
        - application Agent service construction
        - dependency contract validation

    Does not own:
        - Agent construction
        - runtime execution construction
        - transport
    """

    VERSION = "4.0"

    def create(
        self,
        *,
        orchestrator: AgentOrchestrationProtocol,
    ) -> AgentServiceProtocol:
        if not isinstance(
            orchestrator,
            AgentOrchestrationProtocol,
        ):
            raise TypeError(
                "orchestrator must implement "
                "AgentOrchestrationProtocol"
            )

        service = ApplicationAgentService(
            orchestrator=orchestrator,
        )

        if not service.ready():
            raise RuntimeError(
                "application agent service unavailable"
            )

        return service

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationAgentServiceFactory",
]
