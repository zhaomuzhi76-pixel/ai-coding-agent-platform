from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.errors import CoreErrorDetail


@runtime_checkable
class RuntimeErrorDomainBindingProtocol(Protocol):
    """
    Runtime error domain binding contract.

    Responsibility:
        - expose stable domain identity
        - forward failures to the canonical runtime consumer
        - preserve operation and metadata

    Not Responsible:
        - exception classification
        - normalization implementation
        - runtime execution
        - transport formatting
        - application policy
    """

    @property
    def domain(
        self,
    ) -> str:
        ...

    def consume(
        self,
        error: BaseException,
        *,
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
    "RuntimeErrorDomainBindingProtocol",
]
