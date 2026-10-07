from __future__ import annotations

from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)
from backend.runtime.plugin.capability import (
    RuntimeCapability,
)
from backend.runtime.plugins.code_modification.provider import (
    CodeModificationRuntimeCapabilityProvider,
)


class CodeModificationRuntimePlugin:
    """
    Runtime plugin for concrete code-modification execution.
    """

    VERSION = "1.0"

    name = "code_modification"
    version = VERSION

    CAPABILITY = RuntimeCapability(
        category="code_modification",
        name="execute",
        version=VERSION,
    )

    def __init__(
        self,
        provider: CodeModificationProviderProtocol,
    ) -> None:
        self.provider = CodeModificationRuntimeCapabilityProvider(
            provider=provider,
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
    "CodeModificationRuntimePlugin",
]
