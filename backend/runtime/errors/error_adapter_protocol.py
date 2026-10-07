from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.errors import CoreErrorDetail


@runtime_checkable
class RuntimeErrorAdapterProtocol(Protocol):
    """
    Runtime-to-Core error normalization contract.

    Responsibility:
        - normalize runtime failures
        - produce canonical CoreErrorDetail

    Not Responsible:
        - runtime execution
        - transport formatting
        - application policy
        - logging
    """

    def adapt(
        self,
        error: BaseException,
        *,
        operation: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CoreErrorDetail:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...
    

__all__ = [
    "RuntimeErrorAdapterProtocol",
]
