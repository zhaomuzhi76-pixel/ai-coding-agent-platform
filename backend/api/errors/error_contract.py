from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.core.errors import CoreErrorProtocol


@runtime_checkable
class TransportErrorProtocol(Protocol):
    """
    Transport-visible canonical error contract.

    Responsibility:
        - expose normalized transport error payload
        - preserve core error identity
        - preserve session identity

    Not Responsible:
        - exception classification
        - runtime execution
        - application business logic
        - websocket orchestration
    """

    def build(
        self,
        error: CoreErrorProtocol,
        session_id: str,
    ) -> dict[str, Any]:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "TransportErrorProtocol",
]
