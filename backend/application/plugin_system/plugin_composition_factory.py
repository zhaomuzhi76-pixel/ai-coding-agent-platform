from __future__ import annotations

from backend.application.plugin_system.plugin_composition import (
    ApplicationPluginSystemComposition,
)
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


class ApplicationPluginSystemCompositionFactory:
    """
    Sole construction owner for plugin system composition.
    """

    VERSION = "1.0"

    def create(
        self,
    ) -> ApplicationPluginSystemComposition:
        registry = ApplicationPluginRegistry()

        return ApplicationPluginSystemComposition(
            registry=registry,
            loader=ApplicationPluginLoader(
                registry
            ),
            factory=ApplicationPluginFactory(),
            executor=ApplicationPluginExecutor(),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPluginSystemCompositionFactory",
]
