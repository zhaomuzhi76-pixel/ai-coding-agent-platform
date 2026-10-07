from __future__ import annotations

from backend.runtime.bootstrap.tool_runtime_provider import (
    RuntimeToolRuntimeProvider,
)
from backend.runtime.plugins.tools.capability import (
    ToolRuntimeCapability,
)


class ToolRuntimeCapabilityProvider:
    """
    Runtime provider for the canonical ToolRuntime capability.

    The ToolRuntime infrastructure provider is injected so this
    capability never constructs a second ToolRuntime owner.
    """

    VERSION = "2.0"

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
        self._capability: ToolRuntimeCapability | None = None

    def create(
        self,
    ) -> ToolRuntimeCapability:
        if self._capability is not None:
            if not self._capability.ready():
                raise RuntimeError(
                    "tool runtime capability unavailable"
                )
            return self._capability

        runtime = self.runtime_provider.create()

        capability = ToolRuntimeCapability(
            runtime
        )

        if not capability.ready():
            raise RuntimeError(
                "tool runtime capability unavailable"
            )

        self._capability = capability
        return capability

    def ready(
        self,
    ) -> bool:
        return (
            self.runtime_provider.ready()
            and (
                self._capability is None
                or self._capability.ready()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "runtime_created": (
                self._capability is not None
            ),
            "runtime_provider": (
                type(self.runtime_provider).__name__
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ToolRuntimeCapabilityProvider",
]
