from __future__ import annotations

from backend.application.plugin_system.plugin_executor import (
    ApplicationPluginExecutor,
)
from backend.application.plugin_system.plugin_factory import (
    ApplicationPluginFactory,
)
from backend.application.plugin_system.plugin_loader import (
    ApplicationPluginLoader,
)
from backend.application.plugin_system.plugin_registry import (
    ApplicationPluginRegistry,
)


class ApplicationPluginSystemComposition:
    """
    Plugin system composition boundary.

    Owns:
        - plugin infrastructure assembly reference

    Does not own:
        - plugin business logic
        - plugin implementation
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        registry: ApplicationPluginRegistry,
        loader: ApplicationPluginLoader,
        factory: ApplicationPluginFactory,
        executor: ApplicationPluginExecutor,
    ) -> None:
        self.registry = registry
        self.loader = loader
        self.factory = factory
        self.executor = executor

    def ready(self) -> bool:
        return (
            self.registry.ready()
            and self.loader.ready()
            and self.factory.ready()
            and self.executor.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPluginSystemComposition",
]
