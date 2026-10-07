from __future__ import annotations

from typing import Any

from backend.api.errors.error_contract import (
    TransportErrorProtocol,
)


class TransportErrorDelivery:
    """
    Transport error delivery boundary.

    Responsibility:
        - validate transport error capability
        - deliver canonical payload to websocket

    Not Responsible:
        - exception classification
        - error normalization
        - websocket session lifecycle
        - application service execution
    """

    VERSION = "1.0"

    def __init__(
        self,
        adapter: TransportErrorProtocol,
    ) -> None:
        if adapter is None:
            raise ValueError(
                "transport error adapter required"
            )

        if not isinstance(
            adapter,
            TransportErrorProtocol,
        ):
            raise TypeError(
                "invalid transport error adapter"
            )

        if not adapter.ready():
            raise RuntimeError(
                "transport error adapter not ready"
            )

        self.adapter = adapter
        self.delivery_count = 0

    async def send(
        self,
        websocket: Any,
        error,
        session_id: str,
    ) -> None:
        self._validate_websocket(
            websocket
        )

        payload = self.adapter.build(
            error,
            session_id,
        )

        await websocket.send_json(
            payload
        )

        self.delivery_count += 1

    def ready(
        self,
    ) -> bool:
        return (
            self.adapter is not None
            and self.adapter.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "delivery_count": (
                self.delivery_count
            ),
            "ready": self.ready(),
            "adapter": self.adapter.dump(),
        }

    @staticmethod
    def _validate_websocket(
        websocket: Any,
    ) -> None:
        if websocket is None:
            raise ValueError(
                "websocket required"
            )

        if not callable(
            getattr(
                websocket,
                "send_json",
                None,
            )
        ):
            raise TypeError(
                "websocket send_json required"
            )


__all__ = [
    "TransportErrorDelivery",
]
