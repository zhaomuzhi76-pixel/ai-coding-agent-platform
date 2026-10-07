from __future__ import annotations

from backend.runtime.bootstrap.tool_runtime_provider import (
    RuntimeToolRuntimeProvider,
)
from backend.runtime.plugin.capability import (
    RuntimeCapability,
)
from backend.runtime.plugins.tools.provider import (
    ToolRuntimeCapabilityProvider,
)


class ToolRuntimePlugin:
    """
    Runtime plugin for the canonical tool runtime capability.

    The shared RuntimeToolRuntimeProvider is injected so the plugin
    cannot create a second ToolRuntime infrastructure owner.
    """

    VERSION = "2.0"

    name = "tools"
    version = VERSION

    CAPABILITY = RuntimeCapability(
        category="tools",
        name="runtime",
        version=VERSION,
    )

    def __init__(
        self,
        runtime_provider: RuntimeToolRuntimeProvider,
    ) -> None:
        if not isinstance(
            runtime_provider,
            RuntimeToolRuntimeProvider,
        ):
            raise TypeError(
                "runtime_provider must RuntimeToolRuntimeProvider"
            )

        self.runtime_provider = runtime_provider
        self.provider = ToolRuntimeCapabilityProvider(
            runtime_provider
        )

    def capabilities(
        self,
    ) -> list[RuntimeCapability]:
        return [
            self.CAPABILITY,
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
            "runtime_provider": (
                type(self.runtime_provider).__name__
            ),
            "provider": self.provider.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ToolRuntimePlugin",
]
