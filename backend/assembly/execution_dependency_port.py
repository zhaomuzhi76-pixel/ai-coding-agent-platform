from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ExecutionDependencyAssemblyProtocol(Protocol):
    """Application execution-dependency assembly port."""

    def create(
        self,
        *,
        runtime: object,
        workspace: object,
    ) -> object:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ExecutionDependencyAssemblyProtocol",
]
