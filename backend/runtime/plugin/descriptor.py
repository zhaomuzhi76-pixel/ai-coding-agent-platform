from __future__ import annotations

from dataclasses import dataclass

from backend.runtime.plugin.capability_descriptor import (
    RuntimeCapabilityDescriptor,
)
from backend.runtime.plugin.plugin_dependency import (
    RuntimePluginDependency,
)


@dataclass(frozen=True)
class RuntimePluginDescriptor:
    """
    Runtime plugin metadata contract.

    Responsibility:
        - identify plugin
        - describe plugin entry
        - declare capabilities
        - declare capability dependencies

    Not Responsible:
        - loading
        - lifecycle
        - execution
        - dependency resolution
    """

    VERSION = "3.0"

    name: str
    version: str
    category: str = "runtime"
    description: str = ""
    module: str = ""
    entry: str = ""
    capabilities: tuple[
        RuntimeCapabilityDescriptor,
        ...
    ] = ()
    dependencies: tuple[
        RuntimePluginDependency,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("plugin name must str")
        if not self.name.strip():
            raise ValueError(
                "plugin name required"
            )

        if not isinstance(self.version, str):
            raise TypeError("plugin version must str")
        if not self.version.strip():
            raise ValueError(
                "plugin version required"
            )

        if not isinstance(self.category, str):
            raise TypeError(
                "plugin category must str"
            )
        if not self.category.strip():
            raise ValueError(
                "plugin category required"
            )

        if not isinstance(self.module, str):
            raise TypeError(
                "plugin module must str"
            )
        if not self.module.strip():
            raise ValueError(
                "plugin module required"
            )

        if not isinstance(self.entry, str):
            raise TypeError(
                "plugin entry must str"
            )
        if not self.entry.strip():
            raise ValueError(
                "plugin entry required"
            )

        for capability in self.capabilities:
            if not isinstance(
                capability,
                RuntimeCapabilityDescriptor,
            ):
                raise TypeError(
                    "invalid capability descriptor"
                )

        for dependency in self.dependencies:
            if not isinstance(
                dependency,
                RuntimePluginDependency,
            ):
                raise TypeError(
                    "invalid plugin dependency"
                )

    def ready(self) -> bool:
        return bool(
            self.name.strip()
            and self.version.strip()
            and self.category.strip()
            and self.module.strip()
            and self.entry.strip()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
            "module": self.module,
            "entry": self.entry,
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
    "RuntimePluginDescriptor",
]
