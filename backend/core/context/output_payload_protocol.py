from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.payload import Payload


@runtime_checkable
class OutputPayloadProtocol(
    Protocol,
):
    """Execution output payload capability."""

    def dump(
        self,
    ) -> Payload:
        ...


__all__ = [
    "OutputPayloadProtocol",
]
