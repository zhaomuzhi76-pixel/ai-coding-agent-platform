from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.runtime.plugin.capability import RuntimeCapability


@runtime_checkable
class RuntimePluginManagerAccessProtocol(Protocol):
    def discover(self) -> list[object]:
        ...

    def load_all(self) -> list[object]:
        ...

    def ready(self) -> bool:
        ...


@runtime_checkable
class RuntimePluginProviderAccessProtocol(Protocol):
    manager: RuntimePluginManagerAccessProtocol

    def register_capability(
        self,
        capability: RuntimeCapability,
        provider: object,
    ) -> None:
        ...

    def resolve_capability(
        self,
        capability: RuntimeCapability | str,
        version: str | None = None,
    ) -> object:
        ...

    def ready(self) -> bool:
        ...


class RuntimePluginAccess:
    """Canonical Runtime plugin/capability access boundary."""

    VERSION = "2.0"

    def __init__(
        self,
        *,
        plugin_provider: RuntimePluginProviderAccessProtocol,
    ) -> None:
        if not isinstance(
            plugin_provider,
            RuntimePluginProviderAccessProtocol,
        ):
            raise TypeError(
                "plugin provider access contract required"
            )
        if not plugin_provider.ready():
            raise RuntimeError(
                "plugin provider unavailable"
            )
        if not plugin_provider.manager.ready():
            raise RuntimeError(
                "plugin manager unavailable"
            )
        self.plugin_provider = plugin_provider

    def register_capability(
        self,
        capability: RuntimeCapability,
        provider: object,
    ) -> None:
        self.plugin_provider.register_capability(
            capability,
            provider,
        )

    def resolve_capability(
        self,
        capability: RuntimeCapability | str,
        version: str | None = None,
    ) -> object:
        return self.plugin_provider.resolve_capability(
            capability,
            version,
        )

    def discover_plugins(self) -> list[object]:
        return self.plugin_provider.manager.discover()

    def load_plugins(self) -> list[object]:
        return self.plugin_provider.manager.load_all()

    def ready(self) -> bool:
        return (
            self.plugin_provider.ready()
            and self.plugin_provider.manager.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimePluginAccess",
    "RuntimePluginManagerAccessProtocol",
    "RuntimePluginProviderAccessProtocol",
]
