from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)


@runtime_checkable
class ConnectionProtocol(
    Protocol,
):
    """
    WebSocket connection boundary.
    """

    async def accept(
        self,
    ) -> None:
        ...

    async def send(
        self,
        message: dict[str, CoreValue],
    ) -> None:
        ...

    async def close(
        self,
    ) -> None:
        ...


__all__ = [
    "ConnectionProtocol",
]
