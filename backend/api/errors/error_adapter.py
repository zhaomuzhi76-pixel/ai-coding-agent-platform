from __future__ import annotations

from typing import Any

from backend.core.errors import CoreErrorProtocol

from backend.api.errors.error_contract import (
    TransportErrorProtocol,
)


class TransportErrorAdapter(
    TransportErrorProtocol,
):
    """
    Core error to transport payload adapter.

    Responsibility:
        - convert canonical CoreErrorProtocol into
          transport-safe error payload

    Not Responsible:
        - exception normalization
        - runtime error classification
        - websocket delivery
        - application service ownership
    """

    VERSION = "1.0"

    MESSAGE_TYPE = "error"

    def build(
        self,
        error: CoreErrorProtocol,
        session_id: str,
    ) -> dict[str, Any]:
        self._validate(
            error,
            session_id,
        )

        return {
            "type": self.MESSAGE_TYPE,
            "session_id": session_id,
            "code": error.code.value,
            "message": error.message,
            "metadata": dict(
                error.metadata
            ),
        }

    def ready(
        self,
    ) -> bool:
        return bool(
            self.MESSAGE_TYPE
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "message_type": self.MESSAGE_TYPE,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        error: CoreErrorProtocol,
        session_id: str,
    ) -> None:
        if error is None:
            raise ValueError(
                "core error required"
            )

        if not isinstance(
            error,
            CoreErrorProtocol,
        ):
            raise TypeError(
                "error must implement CoreErrorProtocol"
            )

        if not error.ready():
            raise RuntimeError(
                "core error not ready"
            )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )


__all__ = [
    "TransportErrorAdapter",
]
