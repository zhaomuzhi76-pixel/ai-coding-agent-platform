from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.errors import CoreErrorDetail


@runtime_checkable
class RuntimeErrorConsumerProtocol(Protocol):
    """
    Runtime error consumption contract.

    Responsibility:
        - receive runtime failures
        - delegate normalization through a stable boundary
        - expose the canonical normalized error

    Not Responsible:
        - exception classification rules
        - transport formatting
        - runtime execution
        - application policy
        - logging implementation
    """

    def consume(
        self,
        error: BaseException,
        *,
        domain: str,
        operation: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CoreErrorDetail:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "RuntimeErrorConsumerProtocol",
]
