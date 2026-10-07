from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True,
)
class RuntimeSessionEvent:
    """
    Runtime Session event contract.
    """

    event_name: str
    session_id: str
    payload: dict[str, Any]

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return bool(
            self.event_name
            and self.session_id
        )

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "event_name": self.event_name,
            "session_id": self.session_id,
            "payload": self.payload,
            "ready": self.ready(),
        }
