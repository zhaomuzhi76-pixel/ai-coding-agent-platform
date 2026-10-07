from __future__ import annotations

from backend.runtime.plugin.descriptor import (
    RuntimePluginDescriptor,
)
from backend.runtime.plugin.plugin_entry import (
    RuntimePluginEntryProtocol,
)
from backend.runtime.plugin.plugin_manifest import (
    RuntimePluginManifest,
)
from backend.runtime.plugin.plugin_resolver import (
    RuntimePluginResolver,
)


class RuntimePluginLoader:
    """
    Runtime plugin loader.

    Responsibility:
        - convert descriptor to canonical manifest
        - resolve plugin entry
        - validate plugin entry contract

    Not Responsible:
        - discovery
        - lifecycle
        - dependency orchestration
        - capability execution
        - registry management
    """

    VERSION = "7.0"

    def __init__(
        self,
        resolver: RuntimePluginResolver | None = None,
    ) -> None:
        self.resolver = (
            resolver
            or RuntimePluginResolver()
        )
        self.plugins: list[object] = []

    def load_manifest(
        self,
        manifest: RuntimePluginManifest,
    ) -> object:
        if manifest is None:
            raise ValueError(
                "plugin manifest required"
            )

        if not manifest.ready():
            raise ValueError(
                "invalid plugin manifest"
            )

        plugin = self.resolver.resolve(
            manifest
        )

        self._validate(
            plugin
        )

        self.plugins.append(
            plugin
        )

        return plugin

    def load_descriptor(
        self,
        descriptor: RuntimePluginDescriptor,
    ) -> object:
        if descriptor is None:
            raise ValueError(
                "plugin descriptor required"
            )

        if not descriptor.ready():
            raise ValueError(
                "invalid plugin descriptor"
            )

        manifest = RuntimePluginManifest(
            name=descriptor.name,
            version=descriptor.version,
            module=descriptor.module,
            entry=descriptor.entry,
            category=descriptor.category,
            capabilities=descriptor.capabilities,
            dependencies=descriptor.dependencies,
        )

        plugin = self.load_manifest(
            manifest
        )

        binder = getattr(
            plugin,
            "bind_descriptor",
            None,
        )

        if callable(binder):
            binder(descriptor)

        return plugin

    def _validate(
        self,
        plugin: object,
    ) -> None:
        if not isinstance(
            plugin,
            RuntimePluginEntryProtocol,
        ):
            raise TypeError(
                "invalid runtime plugin entry contract"
            )

    def ready(self) -> bool:
        return self.resolver.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "plugins": tuple(
                type(item).__name__
                for item in self.plugins
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimePluginLoader",
]
