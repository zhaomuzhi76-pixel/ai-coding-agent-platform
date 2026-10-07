from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WSAgentResultDeliveryProtocol(Protocol):
    """
    API-facing result delivery port.

    Owns:
        - successful execution delivery
        - terminal execution delivery
        - execution error delivery

    Does not own:
        - execution
        - result creation
        - serialization policy
        - runtime event dispatch
    """

    async def send_result(
        self,
        websocket: object,
        session_id: str,
        model: str,
        result: dict[str, object],
    ) -> None:
        ...

    async def send_error(
        self,
        websocket: object,
        session_id: str,
        message: str,
    ) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "WSAgentResultDeliveryProtocol",
]
