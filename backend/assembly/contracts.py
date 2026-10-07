from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AssemblyModuleProtocol(Protocol):
    name: str
    version: str

    def build(
        self,
        context: Any = None,
    ) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class AssemblyPipelineProtocol(Protocol):
    def build(
        self,
        context: Any = None,
    ) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "AssemblyModuleProtocol",
    "AssemblyPipelineProtocol",
]
