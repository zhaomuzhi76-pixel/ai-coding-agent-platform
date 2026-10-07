from __future__ import annotations

import json


class WSInboundProtocolError(ValueError):
    """WebSocket inbound protocol violation."""


class WSInboundMessageDecoder:
    """
    Decode one WebSocket text frame into a JSON object.

    Owns:
        - frame decoding
        - JSON syntax validation
        - JSON object validation

    Does not own:
        - request translation
        - execution
        - session lifecycle
    """

    VERSION = "1.0"

    async def decode(self, websocket) -> dict[str, object]:
        if websocket is None:
            raise ValueError("websocket required")

        receive_text = getattr(websocket, "receive_text", None)
        if not callable(receive_text):
            raise TypeError("websocket receive_text required")

        try:
            text = await receive_text()
        except Exception as exc:
            raise WSInboundProtocolError(
                "websocket frame receive failed"
            ) from exc

        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise WSInboundProtocolError(
                "invalid JSON payload"
            ) from exc

        if not isinstance(payload, dict):
            raise WSInboundProtocolError(
                "websocket payload must be JSON object"
            )

        return payload

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "WSInboundMessageDecoder",
    "WSInboundProtocolError",
]
