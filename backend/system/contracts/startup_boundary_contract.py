from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SystemStartupProtocol(Protocol):
    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class SystemStartupModuleProtocol(Protocol):
    @property
    def startup(self) -> SystemStartupProtocol:
        ...


@runtime_checkable
class SystemIntegrationRuntimeProtocol(Protocol):
    def start(self) -> object:
        ...

    def stop(self) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "SystemStartupProtocol",
    "SystemStartupModuleProtocol",
    "SystemIntegrationRuntimeProtocol",
]
