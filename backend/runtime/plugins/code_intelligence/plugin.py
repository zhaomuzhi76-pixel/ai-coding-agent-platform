from __future__ import annotations

from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)
from backend.runtime.plugin.capability import (
    RuntimeCapability,
)
from backend.runtime.plugins.code_intelligence.provider import (
    CodeIntelligenceRuntimeCapabilityProvider,
    WorkspaceResolver,
)


class CodeIntelligenceRuntimePlugin:
    """
    Runtime plugin for code intelligence.

    Runtime receives the already-composed Core workspace capability.
    """

    VERSION = "1.0"

    name = "code_intelligence"
    version = VERSION

    CAPABILITY = RuntimeCapability(
        category="code_intelligence",
        name="inspect",
        version=VERSION,
    )

    def __init__(
        self,
        *,
        workspace: CodeIntelligenceWorkspaceProtocol,
        resolver: WorkspaceResolver,
    ) -> None:
        if not isinstance(
            workspace,
            CodeIntelligenceWorkspaceProtocol,
        ):
            raise TypeError(
                "workspace must CodeIntelligenceWorkspaceProtocol"
            )

        if not callable(resolver):
            raise TypeError(
                "code intelligence workspace resolver required"
            )

        self.provider = (
            CodeIntelligenceRuntimeCapabilityProvider(
                workspace=workspace,
                resolver=resolver,
            )
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
    "CodeIntelligenceRuntimePlugin",
]
