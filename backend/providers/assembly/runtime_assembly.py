from __future__ import annotations

from backend.providers.assembly.context import (
    ProviderAssemblyContext,
)
from backend.providers.runtime.execution import (
    ProviderExecutionCoordinator,
)
from backend.providers.runtime.runtime import (
    ProviderRuntime,
)
from backend.providers.runtime.selector import (
    ProviderSelector,
)


class RuntimeAssembly:
    """
    Assemble provider runtime execution components.

    Responsibility:
        - create provider selector
        - create provider execution coordinator
        - create stable provider runtime

    Not Responsible:
        - provider registration
        - capability registration
        - application composition
    """

    VERSION = "2.0"

    def build(
        self,
        context: ProviderAssemblyContext,
        default_provider: str,
    ) -> None:
        if context is None:
            raise ValueError(
                "provider assembly context required"
            )

        if not isinstance(default_provider, str) or not default_provider.strip():
            raise ValueError(
                "configured provider required"
            )

        selector = ProviderSelector(
            context.provider_registry,
            default_provider,
        )

        execution = ProviderExecutionCoordinator(
            context.capability_resolver
        )

        runtime = ProviderRuntime(
            selector,
            execution,
        )

        context.selector = selector
        context.execution = execution
        context.runtime = runtime

    def ready(
        self,
        context: ProviderAssemblyContext,
    ) -> bool:
        return (
            context is not None
            and context.selector is not None
            and context.execution is not None
            and context.runtime is not None
            and context.selector.ready()
            and context.execution.ready()
            and context.runtime.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
        }


__all__ = [
    "RuntimeAssembly",
]
