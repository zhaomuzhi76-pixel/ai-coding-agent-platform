from __future__ import annotations

from dataclasses import dataclass

from backend.runtime.plugin.capability_descriptor import (
    RuntimeCapabilityDescriptor,
)
from backend.runtime.plugin.plugin_dependency import (
    RuntimePluginDependency,
)


@dataclass(frozen=True)
class RuntimePluginManifest:
    """
    Canonical runtime plugin loading manifest.

    Responsibility:
        - carry complete plugin metadata
        - preserve capabilities and dependencies

    Not Responsible:
        - discovery
        - plugin instantiation
        - lifecycle
        - dependency resolution
    """

    VERSION = "3.0"

    name: str
    version: str
    module: str
    entry: str
    category: str = "runtime"
    capabilities: tuple[
        RuntimeCapabilityDescriptor,
        ...
    ] = ()
    dependencies: tuple[
        RuntimePluginDependency,
        ...
    ] = ()

    def __post_init__(self) -> None:
        fields = (
            ("name", self.name),
            ("version", self.version),
            ("module", self.module),
            ("entry", self.entry),
            ("category", self.category),
        )

        for field_name, value in fields:
            if not isinstance(value, str):
                raise TypeError(
                    f"plugin {field_name} must str"
                )
            if not value.strip():
                raise ValueError(
                    f"plugin {field_name} required"
                )

        for item in self.capabilities:
            if not isinstance(
                item,
                RuntimeCapabilityDescriptor,
            ):
                raise TypeError(
                    "invalid capability descriptor"
                )

        for item in self.dependencies:
            if not isinstance(
                item,
                RuntimePluginDependency,
            ):
                raise TypeError(
                    "invalid plugin dependency"
                )

    def ready(self) -> bool:
        return bool(
            self.name.strip()
            and self.version.strip()
            and self.module.strip()
            and self.entry.strip()
            and self.category.strip()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "module": self.module,
            "entry": self.entry,
            "category": self.category,
            "capabilities": tuple(
                item.dump()
                for item in self.capabilities
            ),
            "dependencies": tuple(
                item.dump()
                for item in self.dependencies
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimePluginManifest",
]
