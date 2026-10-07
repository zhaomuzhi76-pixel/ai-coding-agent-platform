from __future__ import annotations

from backend.runtime.plugin.capability import (
    RuntimeCapability,
)

from backend.runtime.plugins.intelligence.provider import (
    IntelligenceGovernanceCapabilityProvider,
)

from backend.runtime.plugins.intelligence.memory_provider import (
    IntelligenceMemoryCapabilityProvider,
)


class IntelligenceRuntimePlugin:
    """
    Runtime intelligence plugin.

    Responsibility:
        - publish intelligence capabilities
        - own capability providers

    Not Responsible:
        - governance algorithm
        - memory storage
        - persistence
        - retrieval
    """

    VERSION = "1.0"

    name = "intelligence"
    version = VERSION

    CAPABILITY = RuntimeCapability(
        category="intelligence",
        name="governance",
        version=VERSION,
    )

    MEMORY_CAPABILITY = RuntimeCapability(
        category="intelligence",
        name="memory",
        version=VERSION,
    )

    def __init__(
        self,
    ) -> None:

        self.provider = (
            IntelligenceGovernanceCapabilityProvider()
        )

        self.memory_provider = (
            IntelligenceMemoryCapabilityProvider()
        )

    def capabilities(
        self,
    ) -> list[RuntimeCapability]:

        return [
            self.CAPABILITY,
            self.MEMORY_CAPABILITY,
        ]

    def register(
        self,
        registry,
    ) -> None:

        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        registry.register(
            self.CAPABILITY,
            self.provider,
        )

        registry.register(
            self.MEMORY_CAPABILITY,
            self.memory_provider,
        )

    def ready(
        self,
    ) -> bool:

        return all(
            (
                self.provider.ready(),
                self.memory_provider.ready(),
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.name,
            "version": self.version,
            "capabilities": tuple(
                item.key()
                for item in self.capabilities()
            ),
            "provider": self.provider.dump(),
            "memory": self.memory_provider.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceRuntimePlugin",
]
