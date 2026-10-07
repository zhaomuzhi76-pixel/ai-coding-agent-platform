from __future__ import annotations

from backend.runtime.plugin.capability_registry import (
    RuntimeCapabilityRegistry,
)
from backend.runtime.plugin.controller import (
    RuntimePluginController,
)
from backend.runtime.plugin.dependency_resolver import (
    RuntimePluginDependencyResolver,
)
from backend.runtime.plugin.discovery import (
    RuntimePluginDiscovery,
)
from backend.runtime.plugin.loader import (
    RuntimePluginLoader,
)
from backend.runtime.plugin.plugin_load_transaction import (
    RuntimePluginLoadTransaction,
)
from backend.runtime.plugin.plugin_lifecycle import (
    RuntimePluginLifecycle,
)
from backend.runtime.plugin.registry import (
    RuntimePluginRegistry,
)


class RuntimePluginManager:
    """
    Runtime plugin discovery and assembly boundary.

    Responsibility:
        - discover plugins
        - validate dependencies
        - load plugins
        - coordinate transactional assembly
        - register completed plugins

    Not Responsible:
        - capability implementation
        - execution orchestration
        - business behavior
    """

    VERSION = "15.0"

    def __init__(
        self,
        *,
        registry: RuntimePluginRegistry,
        loader: RuntimePluginLoader,
        controller: RuntimePluginController,
        discovery: RuntimePluginDiscovery,
        capability_registry: RuntimeCapabilityRegistry,
        dependency_resolver: (
            RuntimePluginDependencyResolver | None
        ) = None,
        lifecycle: RuntimePluginLifecycle | None = None,
    ) -> None:
        dependencies = {
            "registry": registry,
            "loader": loader,
            "controller": controller,
            "discovery": discovery,
            "capability_registry": capability_registry,
        }

        for name, value in dependencies.items():
            if value is None:
                raise ValueError(
                    f"{name} required"
                )

        self.registry = registry
        self.loader = loader
        self.controller = controller
        self.discovery = discovery
        self.capability_registry = (
            capability_registry
        )
        self.dependency_resolver = (
            dependency_resolver
            or RuntimePluginDependencyResolver(
                capability_registry
            )
        )
        self.lifecycle = (
            lifecycle
            or RuntimePluginLifecycle()
        )
        self.load_transaction = (
            RuntimePluginLoadTransaction(
                self.lifecycle
            )
        )

    def discover(self) -> list:
        return self.discovery.discover()

    def load_all(self) -> list[object]:
        plugins: list[object] = []

        for descriptor in self.discover():
            self._validate_descriptor(
                descriptor
            )

            if not self.dependency_resolver.validate(
                descriptor.dependencies
            ):
                raise RuntimeError(
                    "plugin dependencies unavailable: "
                    f"{descriptor.name}"
                )

            existing = None
            try:
                existing = self.registry.resolve(
                    descriptor.category,
                    descriptor.name,
                )
            except LookupError:
                existing = None

            if existing is not None:
                plugins.append(existing)
                continue

            plugin = (
                self.loader.load_descriptor(
                    descriptor
                )
            )

            try:
                self.load_transaction.load(
                    plugin_name=descriptor.name,
                    plugin=plugin,
                )

                plugin.register(
                    self.capability_registry
                )

                self.registry.register(
                    category=descriptor.category,
                    name=descriptor.name,
                    component=plugin,
                    version=descriptor.version,
                )
            except Exception:
                self.load_transaction.rollback(
                    plugin_name=descriptor.name,
                    plugin=plugin,
                )
                raise

            plugins.append(plugin)

        return plugins

    def resolve(
        self,
        category: str,
        name: str,
    ) -> object:
        return self.registry.resolve(
            category,
            name,
        )

    def ready(self) -> bool:
        return all(
            (
                self.registry.ready(),
                self.loader.ready(),
                self.controller.ready(),
                self.discovery.ready(),
                self.capability_registry.ready(),
                self.dependency_resolver.ready(),
                self.lifecycle.ready(),
                self.load_transaction.ready(),
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "plugins": self.registry.names(),
            "controller": self.controller.dump(),
            "capabilities": (
                self.capability_registry.dump()
            ),
            "dependency_resolver": (
                self.dependency_resolver.dump()
            ),
            "lifecycle": self.lifecycle.dump(),
            "load_transaction": (
                self.load_transaction.dump()
            ),
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_descriptor(
        descriptor,
    ) -> None:
        if descriptor is None:
            raise ValueError(
                "plugin descriptor required"
            )

        if not descriptor.ready():
            raise RuntimeError(
                "plugin descriptor not ready: "
                f"{descriptor.name}"
            )


__all__ = [
    "RuntimePluginManager",
]
