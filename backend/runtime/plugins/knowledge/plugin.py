from __future__ import annotations

from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.plugins.knowledge.provider import (
    KnowledgeRuntimeCapabilityProvider,
)


class KnowledgeRuntimePlugin:
    """
    Builtin persistent knowledge runtime plugin.

    Responsibility:
        - publish the knowledge runtime capability
        - bind the capability provider

    Not Responsible:
        - request execution
        - knowledge persistence internals
        - planner implementation
        - runtime lifecycle
    """

    VERSION = "1.0"

    name = "knowledge"
    version = VERSION

    CAPABILITY = RuntimeCapability(
        category="knowledge",
        name="runtime",
        version=VERSION,
    )

    def __init__(self) -> None:
        self.provider = (
            KnowledgeRuntimeCapabilityProvider()
        )

    def capabilities(
        self,
    ) -> list[RuntimeCapability]:
        return [self.CAPABILITY]

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

    def ready(
        self,
    ) -> bool:
        return self.provider.ready()

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
            "ready": self.ready(),
        }


__all__ = [
    "KnowledgeRuntimePlugin",
]
