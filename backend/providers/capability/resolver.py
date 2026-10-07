from __future__ import annotations

import inspect
from typing import Any

from backend.providers.capability.registry import (
    ProviderCapabilityRegistry,
)


class ProviderCapabilityResolver:
    """
    Resolve provider capabilities without exposing registry
    implementation details.

    Awaitable results are awaited.
    Async iterators are returned unchanged.
    """

    VERSION = "1.1"

    def __init__(
        self,
        registry: ProviderCapabilityRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "provider capability registry required"
            )
        self.registry = registry

    def resolve(
        self,
        provider: str,
        capability: str,
    ):
        return self.registry.resolve(
            provider,
            capability,
        )

    async def execute(
        self,
        provider: str,
        capability: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        target = self.resolve(
            provider,
            capability,
        )

        if not target.ready():
            raise RuntimeError(
                "provider capability unavailable: "
                f"{provider}.{capability}"
            )

        result = target.execute(
            *args,
            **kwargs,
        )

        if inspect.isawaitable(result):
            return await result

        return result

    def exists(
        self,
        provider: str,
        capability: str,
    ) -> bool:
        return self.registry.exists(
            provider,
            capability,
        )

    def ready(self) -> bool:
        return self.registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "registry": self.registry.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ProviderCapabilityResolver",
]
