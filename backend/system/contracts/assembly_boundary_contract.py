from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SystemAssemblyModuleProtocol(Protocol):
    """Minimal startup-module contract consumed by System."""

    def build(
        self,
        context: Any = None,
    ) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...

    def shutdown(self) -> None:
        ...


@runtime_checkable
class SystemAssemblyRuntimeProtocol(Protocol):
    """Minimal assembled-runtime contract consumed by System."""

    def available(self) -> bool:
        ...

    def start(
        self,
        context: Any = None,
    ) -> Any:
        ...

    def stop(self) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "SystemAssemblyModuleProtocol",
    "SystemAssemblyRuntimeProtocol",
]
