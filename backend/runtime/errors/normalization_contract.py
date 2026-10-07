from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.errors import CoreErrorDetail


@runtime_checkable
class RuntimeErrorNormalizationProtocol(Protocol):
    """
    Canonical runtime error normalization boundary.

    Responsibility:
        - accept runtime failures
        - normalize them into CoreErrorDetail
        - preserve operation and structured metadata

    Not Responsible:
        - exception classification rules
        - transport formatting
        - runtime execution
        - application policy
        - logging
    """

    def normalize(
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
    "RuntimeErrorNormalizationProtocol",
]
