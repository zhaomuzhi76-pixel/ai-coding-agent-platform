from __future__ import annotations

from backend.api.ws_message import build_error_message


class WSProtocolErrorDelivery:
    """
    Deliver transport protocol errors without terminating the WS session.
    """

    VERSION = "1.0"

    async def send(
        self,
        websocket,
        session_id: str,
        message: str,
    ) -> None:
        if websocket is None:
            raise ValueError("websocket required")

        send_json = getattr(websocket, "send_json", None)
        if not callable(send_json):
            raise TypeError("websocket send_json required")

        await send_json(
            build_error_message(
                session_id,
                message,
            )
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "WSProtocolErrorDelivery",
]
