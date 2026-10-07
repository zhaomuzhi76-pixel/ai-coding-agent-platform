from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CodeModificationProviderProtocol(Protocol):
    """
    Core contract for asynchronous code-modification execution.

    Application may compose proposal generation with the runtime
    modification pipeline. Runtime consumes only this contract.
    """

    async def execute(
        self,
        *,
        task: str,
        files: list[str],
        context: dict[str, Any],
    ) -> object:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "CodeModificationProviderProtocol",
]
