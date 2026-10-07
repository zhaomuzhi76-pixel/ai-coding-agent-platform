from __future__ import annotations

import importlib
from typing import Any

from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.plugin.capability_descriptor import (
    RuntimeCapabilityDescriptor,
)
from backend.runtime.plugin.capability_registry import (
    RuntimeCapabilityRegistry,
)


class RuntimeCapabilityLoader:
    """
    Load a runtime capability provider instance.

    Responsibility:
        - resolve provider entry from descriptor
        - construct the provider instance
        - validate the provider execution boundary
        - register the canonical instance

    Not Responsible:
        - plugin discovery
        - plugin lifecycle
        - business implementation
    """

    VERSION = "2.0"

    def __init__(
        self,
        registry: RuntimeCapabilityRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        self.registry = registry
        self.load_count = 0

    def load(
        self,
        descriptor: RuntimeCapabilityDescriptor,
    ) -> object:
        self._validate_descriptor(descriptor)

        module_name, entry_name = self._split_entry(
            descriptor.entry
        )

        module = importlib.import_module(module_name)
        entry = getattr(
            module,
            entry_name,
            None,
        )

        if entry is None:
            raise RuntimeError(
                "capability provider entry unavailable: "
                f"{descriptor.entry}"
            )

        provider = self._create_provider(
            entry,
            descriptor.entry,
        )

        self._validate_provider(
            provider,
            descriptor.entry,
        )

        capability = RuntimeCapability(
            category=descriptor.category,
            name=descriptor.name,
            version=descriptor.version,
        )

        self.registry.register(
            capability,
            provider,
        )

        self.load_count += 1
        return provider

    def ready(
        self,
    ) -> bool:
        return self.registry.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "load_count": self.load_count,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_descriptor(
        descriptor: RuntimeCapabilityDescriptor,
    ) -> None:
        if descriptor is None:
            raise ValueError(
                "capability descriptor required"
            )

        if not isinstance(
            descriptor,
            RuntimeCapabilityDescriptor,
        ):
            raise TypeError(
                "descriptor must RuntimeCapabilityDescriptor"
            )

        if not descriptor.ready():
            raise ValueError(
                "invalid capability descriptor"
            )

    @staticmethod
    def _split_entry(
        entry: str,
    ) -> tuple[str, str]:
        if not isinstance(entry, str):
            raise TypeError(
                "capability entry must str"
            )

        normalized = entry.strip()

        if not normalized or "." not in normalized:
            raise ValueError(
                "capability entry must be module.Class"
            )

        module_name, class_name = normalized.rsplit(
            ".",
            1,
        )

        if not module_name or not class_name:
            raise ValueError(
                "invalid capability entry"
            )

        return module_name, class_name

    @staticmethod
    def _create_provider(
        entry: Any,
        entry_name: str,
    ) -> object:
        if isinstance(entry, type):
            try:
                return entry()
            except TypeError as error:
                raise TypeError(
                    "capability provider class must "
                    "be constructible without arguments: "
                    f"{entry_name}"
                ) from error

        return entry

    @staticmethod
    def _validate_provider(
        provider: object,
        entry_name: str,
    ) -> None:
        if provider is None:
            raise TypeError(
                "capability provider unavailable: "
                f"{entry_name}"
            )

        execute = getattr(
            provider,
            "execute",
            None,
        )
        ready = getattr(
            provider,
            "ready",
            None,
        )
        dump = getattr(
            provider,
            "dump",
            None,
        )

        if not callable(execute):
            raise TypeError(
                "capability provider execute missing: "
                f"{entry_name}"
            )

        if not callable(ready):
            raise TypeError(
                "capability provider ready missing: "
                f"{entry_name}"
            )

        if not callable(dump):
            raise TypeError(
                "capability provider dump missing: "
                f"{entry_name}"
            )

        if not ready():
            raise RuntimeError(
                "capability provider not ready: "
                f"{entry_name}"
            )


__all__ = [
    "RuntimeCapabilityLoader",
]
