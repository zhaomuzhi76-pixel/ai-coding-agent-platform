from __future__ import annotations

from typing import Any

from backend.api.ws_message import (
    build_end_message,
    build_error_message,
    build_result_message,
)


class WSMessageSender:
    """
    WebSocket payload delivery boundary.

    Owns:
        - result/end/error delivery
        - closed-connection send suppression

    Does not own:
        - message construction
        - execution
        - connection lifecycle
    """

    VERSION = "3.1"
    CLOSED_SEND_MARKERS = (
        "close message has been sent",
        "websocket is disconnected",
        "websocket is not connected",
    )

    async def send_result(
        self,
        websocket,
        session_id: str,
        model: str,
        result: Any,
    ) -> None:
        self._validate_websocket(websocket)

        delivered = await self._safe_send(
            websocket,
            build_result_message(
                session_id,
                model,
                result,
            ),
        )

        if delivered:
            await self._safe_send(
                websocket,
                build_end_message(
                    session_id,
                    model,
                ),
            )

    async def send_error(
        self,
        websocket,
        session_id: str,
        message: str,
    ) -> None:
        self._validate_websocket(websocket)

        await self._safe_send(
            websocket,
            build_error_message(
                session_id,
                message,
            ),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    async def _safe_send(
        self,
        websocket,
        payload: dict[str, Any],
    ) -> bool:
        try:
            await websocket.send_json(payload)
            return True
        except RuntimeError as error:
            if self._is_closed_send_error(error):
                return False
            raise

    @classmethod
    def _is_closed_send_error(
        cls,
        error: RuntimeError,
    ) -> bool:
        message = str(error).lower()
        return any(
            marker in message
            for marker in cls.CLOSED_SEND_MARKERS
        )

    @staticmethod
    def _validate_websocket(
        websocket,
    ) -> None:
        if websocket is None:
            raise ValueError(
                "websocket required"
            )

        if not callable(
            getattr(websocket, "send_json", None)
        ):
            raise TypeError(
                "websocket send_json required"
            )


__all__ = [
    "WSMessageSender",
]
