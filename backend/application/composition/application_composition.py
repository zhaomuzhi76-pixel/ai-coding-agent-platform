from __future__ import annotations

from typing import Any

from backend.application.composition.runtime import (
    ApplicationRuntimeComposition,
)
from backend.application.modules.registry import (
    ApplicationModuleRegistry,
)


class ApplicationComposition:
    """
    Application composition root boundary.

    Owns:
        - application module registry binding
        - runtime composition binding
        - module resolution boundary

    Does not own:
        - module construction
        - runtime implementation
        - provider implementation
    """

    VERSION = "2.0"

    def __init__(
        self,
        registry: ApplicationModuleRegistry,
        runtime: ApplicationRuntimeComposition,
    ) -> None:
        if not isinstance(
            registry,
            ApplicationModuleRegistry,
        ):
            raise TypeError(
                "invalid application registry"
            )

        if not isinstance(
            runtime,
            ApplicationRuntimeComposition,
        ):
            raise TypeError(
                "invalid runtime composition"
            )

        if not registry.ready():
            raise RuntimeError(
                "application registry unavailable"
            )

        if not runtime.ready():
            raise RuntimeError(
                "runtime composition unavailable"
            )

        self.registry = registry
        self.runtime = runtime

    def resolve_module(
        self,
        name: str,
    ) -> Any:
        return self.registry.get_module(
            name,
        )

    def create_runtime(
        self,
    ) -> object:
        return self.runtime.create()

    def ready(
        self,
    ) -> bool:
        return (
            self.registry.ready()
            and self.runtime.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registry": self.registry.dump(),
            "runtime": self.runtime.dump(),
        }


__all__ = [
    "ApplicationComposition",
]
