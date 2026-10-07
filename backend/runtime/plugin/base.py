from __future__ import annotations

from abc import ABC

from backend.runtime.plugin.capability import (
    RuntimeCapability,
)
from backend.runtime.plugin.descriptor import (
    RuntimePluginDescriptor,
)


class RuntimePluginBase(
    ABC,
):
    """
    Base implementation for runtime plugins.

    Responsibility:
        - stable plugin lifecycle hooks
        - descriptor binding
        - entry contract defaults

    Not Responsible:
        - plugin discovery
        - plugin loading
        - capability registry ownership
        - business execution
    """

    VERSION = "2.0"

    def __init__(self) -> None:
        self._descriptor: (
            RuntimePluginDescriptor | None
        ) = None

    @property
    def name(self) -> str:
        if self._descriptor is not None:
            return self._descriptor.name
        return self.__class__.__name__

    @property
    def version(self) -> str:
        if self._descriptor is not None:
            return self._descriptor.version
        return self.VERSION

    def bind_descriptor(
        self,
        descriptor: RuntimePluginDescriptor,
    ) -> None:
        if descriptor is None:
            raise ValueError(
                "plugin descriptor required"
            )

        if not descriptor.ready():
            raise ValueError(
                "invalid plugin descriptor"
            )

        self._descriptor = descriptor

    @property
    def descriptor(
        self,
    ) -> RuntimePluginDescriptor:
        if self._descriptor is None:
            raise RuntimeError(
                "plugin descriptor not bound"
            )

        return self._descriptor

    def capabilities(
        self,
    ) -> list[RuntimeCapability]:
        if self._descriptor is None:
            return []

        return [
            RuntimeCapability(
                category=item.category,
                name=item.name,
                version=item.version,
            )
            for item in self._descriptor.capabilities
        ]

    def register(
        self,
        registry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "capability registry required"
            )

    def install(
        self,
    ) -> None:
        return None

    def enable(
        self,
    ) -> None:
        return None

    def disable(
        self,
    ) -> None:
        return None

    def unload(
        self,
    ) -> None:
        return None

    def ready(
        self,
    ) -> bool:
        return bool(
            self.name
            and self.version
        )

    def dump(
        self,
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "capabilities": tuple(
                item.key()
                for item in self.capabilities()
            ),
        }

        if self._descriptor is not None:
            result["descriptor"] = (
                self._descriptor.dump()
            )

        return result


__all__ = [
    "RuntimePluginBase",
]
