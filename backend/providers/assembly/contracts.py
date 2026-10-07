from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProviderAssemblyProtocol(Protocol):
    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class ProviderAssemblyBuilderProtocol(Protocol):
    def build(self):
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...
