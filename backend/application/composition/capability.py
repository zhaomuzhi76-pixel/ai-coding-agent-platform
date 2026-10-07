from __future__ import annotations

from backend.application.agent_service import (
    ApplicationAgentService,
)
from backend.application.capability.agent_adapter import (
    ApplicationAgentCapabilityAdapter,
)
from backend.application.capability.agent_adapter_factory import (
    ApplicationAgentCapabilityAdapterFactory,
)
from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.manager_factory import (
    ApplicationCapabilityManagerFactory,
)


class ApplicationCapabilityComposition:
    """
    Application capability assembly boundary.

    The application capability layer exposes stable application
    capabilities. Submission execution is represented by the
    canonical RuntimeSubmission boundary rather than a parallel
    submission capability.
    """

    VERSION = "2.0"

    AGENT_DESCRIPTOR = ApplicationCapabilityDescriptor(
        name="agent.execution",
        version="1.0",
        category="application",
        capabilities=("agent.execute",),
    )

    def create(self) -> ApplicationCapabilityManager:
        manager = (
            ApplicationCapabilityManagerFactory()
            .create()
        )

        if not manager.ready():
            raise RuntimeError(
                "application capability manager unavailable"
            )

        return manager

    def install_agent(
        self,
        manager: ApplicationCapabilityManager,
        service: ApplicationAgentService,
    ) -> ApplicationAgentCapabilityAdapter:
        if manager is None or not manager.ready():
            raise RuntimeError(
                "capability manager not ready"
            )

        if service is None or not service.ready():
            raise RuntimeError(
                "agent service not ready"
            )

        capability = manager.install(
            descriptor=self.AGENT_DESCRIPTOR,
            implementation=(
                ApplicationAgentCapabilityAdapterFactory()
                .create(
                    service=service,
                )
            ),
        )

        if not capability.ready():
            raise RuntimeError(
                "agent capability unavailable"
            )

        manager.enable(
            self.AGENT_DESCRIPTOR.name
        )
        return capability

    def resolve_agent(
        self,
        manager: ApplicationCapabilityManager,
    ) -> ApplicationAgentCapabilityAdapter:
        capability = manager.resolve(
            self.AGENT_DESCRIPTOR.key()
        )

        if not isinstance(
            capability,
            ApplicationAgentCapabilityAdapter,
        ):
            raise TypeError(
                "agent capability implementation invalid"
            )

        return capability

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
            "agent_descriptor": (
                self.AGENT_DESCRIPTOR.dump()
            ),
        }


__all__ = [
    "ApplicationCapabilityComposition",
]
