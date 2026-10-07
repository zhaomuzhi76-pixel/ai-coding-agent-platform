from __future__ import annotations

from backend.providers.assembly.context import (
    ProviderAssemblyContext,
)
from backend.providers.assembly.runtime import (
    ProviderAssemblyRuntime,
)


class ProviderAssemblyRuntimeFactory:
    """
    Construct the stable provider assembly runtime boundary.

    Responsibility:
        - validate assembled provider context
        - construct ProviderAssemblyRuntime

    Not Responsible:
        - provider registration
        - provider capability binding
        - provider selection
        - provider execution
        - application composition
    """

    VERSION = "1.0"

    def create(
        self,
        context: ProviderAssemblyContext,
    ) -> ProviderAssemblyRuntime:
        if context is None:
            raise ValueError(
                "provider assembly context required"
            )

        if not context.ready():
            raise RuntimeError(
                "provider assembly context not ready"
            )

        runtime = ProviderAssemblyRuntime(
            context
        )

        if not runtime.ready():
            raise RuntimeError(
                "provider assembly runtime unavailable"
            )

        return runtime

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProviderAssemblyRuntimeFactory",
]
