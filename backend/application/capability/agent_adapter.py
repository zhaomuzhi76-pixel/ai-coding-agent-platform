from __future__ import annotations

from backend.application.agent_service_contract import (
    AgentServiceProtocol,
)
from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class ApplicationAgentCapabilityAdapter(
    ApplicationCapabilityProtocol,
):
    """
    Capability adapter for the application agent execution service.

    Ownership:
        - expose the application agent execution capability
        - own capability identity and lifecycle state
        - delegate execution to AgentServiceProtocol

    Not Responsible:
        - agent construction
        - application service construction
        - runtime construction
        - execution implementation
        - capability storage
        - capability lifecycle orchestration
    """

    VERSION = "1.0"
    NAME = "agent.execution"

    def __init__(
        self,
        service: AgentServiceProtocol,
    ) -> None:
        if service is None:
            raise ValueError(
                "agent service required"
            )

        if not isinstance(
            service,
            AgentServiceProtocol,
        ):
            raise TypeError(
                "service must implement AgentServiceProtocol"
            )

        self.service = service
        self.initialized = False
        self.shutdown_count = 0

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    def capabilities(self) -> tuple[str, ...]:
        return (
            "agent.execute",
        )

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        if not self.initialized:
            raise RuntimeError(
                "agent execution capability not enabled"
            )

        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must be AgentRequest"
            )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )

        result = await self.service.execute(
            request,
            session_id,
        )

        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "agent service must return ExecutionResult"
            )

        return result

    def initialize(
        self,
        context: object = None,
    ) -> None:
        if not self.service_ready():
            raise RuntimeError(
                "agent service not ready"
            )

        self.initialized = True

    def shutdown(
        self,
    ) -> None:
        self.initialized = False
        self.shutdown_count += 1

    def ready(
        self,
    ) -> bool:
        return self.service_ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
            "initialized": self.initialized,
            "shutdown_count": self.shutdown_count,
            "service": type(
                self.service
            ).__name__,
            "service_ready": self.service_ready(),
            "ready": self.ready(),
        }

    def service_ready(
        self,
    ) -> bool:
        return bool(
            self.service.ready()
        )


__all__ = [
    "ApplicationAgentCapabilityAdapter",
]
