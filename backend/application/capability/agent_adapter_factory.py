from __future__ import annotations

from backend.application.agent_service_contract import (
    AgentServiceProtocol,
)
from backend.application.capability.agent_adapter import (
    ApplicationAgentCapabilityAdapter,
)


class ApplicationAgentCapabilityAdapterFactory:
    """
    Sole construction owner for
    ApplicationAgentCapabilityAdapter.
    """

    VERSION = "1.1"

    def create(
        self,
        *,
        service: AgentServiceProtocol,
    ) -> ApplicationAgentCapabilityAdapter:
        if not self.ready():
            raise RuntimeError(
                "agent capability adapter factory unavailable"
            )

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

        adapter = ApplicationAgentCapabilityAdapter(
            service
        )

        if not adapter.ready():
            raise RuntimeError(
                "agent capability adapter unavailable"
            )

        return adapter

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
    "ApplicationAgentCapabilityAdapterFactory",
]
