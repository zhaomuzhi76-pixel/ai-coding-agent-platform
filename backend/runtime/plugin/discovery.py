from __future__ import annotations

import json
from pathlib import Path

from backend.runtime.plugin.capability_descriptor import (
    RuntimeCapabilityDescriptor,
)
from backend.runtime.plugin.descriptor import (
    RuntimePluginDescriptor,
)
from backend.runtime.plugin.plugin_dependency import (
    RuntimePluginDependency,
)


class RuntimePluginDiscovery:
    """
    Runtime plugin discovery boundary.

    Responsibility:
        - discover plugin manifests
        - parse complete plugin metadata

    Not Responsible:
        - loading
        - lifecycle
        - dependency resolution
        - execution
    """

    VERSION = "5.0"

    def __init__(
        self,
        plugin_root: str | Path,
    ) -> None:
        if plugin_root is None:
            raise ValueError(
                "plugin root required"
            )

        self.plugin_root = Path(plugin_root)
        self.plugins: list[
            RuntimePluginDescriptor
        ] = []

    def discover(
        self,
    ) -> list[RuntimePluginDescriptor]:
        self.plugins.clear()

        if not self.plugin_root.exists():
            return self.plugins

        for manifest in self.plugin_root.rglob(
            "plugin.json"
        ):
            descriptor = self._load_manifest(
                manifest
            )
            self.plugins.append(descriptor)

        return list(self.plugins)

    def _load_manifest(
        self,
        path: Path,
    ) -> RuntimePluginDescriptor:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return RuntimePluginDescriptor(
            name=data.get(
                "name",
                path.parent.name,
            ),
            version=data.get(
                "version",
                "1.0",
            ),
            category=data.get(
                "category",
                "runtime",
            ),
            description=data.get(
                "description",
                "",
            ),
            module=data.get(
                "module",
                "",
            ),
            entry=data.get(
                "entry",
                "",
            ),
            capabilities=tuple(
                self._parse_capability(item)
                for item in data.get(
                    "capabilities",
                    [],
                )
            ),
            dependencies=tuple(
                self._parse_dependency(item)
                for item in data.get(
                    "dependencies",
                    [],
                )
            ),
        )

    @staticmethod
    def _parse_capability(
        data: dict[str, object],
    ) -> RuntimeCapabilityDescriptor:
        return RuntimeCapabilityDescriptor(
            category=str(
                data.get(
                    "category",
                    "runtime",
                )
            ),
            name=str(
                data.get(
                    "name",
                    "",
                )
            ),
            version=str(
                data.get(
                    "version",
                    "1.0",
                )
            ),
            entry=str(
                data.get(
                    "entry",
                    "",
                )
            ),
        )

    @staticmethod
    def _parse_dependency(
        data: dict[str, object],
    ) -> RuntimePluginDependency:
        return RuntimePluginDependency(
            capability=str(
                data.get(
                    "capability",
                    "",
                )
            ),
            version=str(
                data.get(
                    "version",
                    ">=1.0",
                )
            ),
        )

    def ready(self) -> bool:
        return self.plugin_root.exists()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "root": str(self.plugin_root),
            "plugins": tuple(
                item.name
                for item in self.plugins
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimePluginDiscovery",
]
