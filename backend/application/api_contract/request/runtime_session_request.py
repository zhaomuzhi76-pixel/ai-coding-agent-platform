from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True,
)
class RuntimeSessionRequest:
    """
    Runtime Session API request contract.
    """

    session_id: str
    command: str
    payload: dict[str, Any]

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return bool(
            self.session_id
            and self.command
        )

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "session_id": self.session_id,
            "command": self.command,
            "payload": self.payload,
            "ready": self.ready(),
        }
