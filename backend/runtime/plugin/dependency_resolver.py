from __future__ import annotations

import re

from backend.runtime.plugin.plugin_dependency import (
    RuntimePluginDependency,
    RuntimePluginDependencySet,
)


class RuntimePluginDependencyResolver:
    """
    Runtime plugin dependency gate.

    Responsibility:
        - resolve declared capability dependencies
        - validate required versions

    Not Responsible:
        - plugin discovery
        - plugin loading
        - lifecycle
        - capability registration
        - execution
    """

    VERSION = "1.0"

    def __init__(
        self,
        capability_registry,
    ) -> None:
        if capability_registry is None:
            raise ValueError(
                "capability registry required"
            )

        self.capability_registry = (
            capability_registry
        )

    def validate(
        self,
        dependencies: tuple[
            RuntimePluginDependency,
            ...
        ]
        | list[RuntimePluginDependency]
        | None,
    ) -> bool:
        dependency_set = (
            RuntimePluginDependencySet(
                list(dependencies or [])
            )
        )

        if not dependency_set.ready():
            return False

        return all(
            self._validate_dependency(
                dependency
            )
            for dependency
            in dependency_set.dependencies
        )

    def _validate_dependency(
        self,
        dependency: RuntimePluginDependency,
    ) -> bool:
        versions = self._versions(
            dependency.capability
        )

        if not versions:
            return False

        minimum = self._minimum_version(
            dependency.version
        )

        if minimum is None:
            return True

        return any(
            self._version_key(version)
            >= self._version_key(minimum)
            for version in versions
        )

    def _versions(
        self,
        capability: str,
    ) -> tuple[str, ...]:
        mapping = self.capability_registry.list()
        return tuple(
            mapping.get(
                capability,
                (),
            )
        )

    @staticmethod
    def _minimum_version(
        expression: str,
    ) -> str | None:
        match = re.fullmatch(
            r"\s*>=\s*([0-9]+(?:\.[0-9]+){0,2})\s*",
            expression or "",
        )
        if match is None:
            return None

        return match.group(1)

    @staticmethod
    def _version_key(
        version: str,
    ) -> tuple[int, int, int]:
        parts = [
            int(item)
            for item in version.split(".")
            if item.isdigit()
        ]

        return tuple(
            (parts + [0, 0, 0])[:3]
        )

    def ready(self) -> bool:
        return self.capability_registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimePluginDependencyResolver",
]
