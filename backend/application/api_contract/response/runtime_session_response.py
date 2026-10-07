from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True,
)
class RuntimeSessionResponse:
    """
    Runtime Session API response contract.
    """

    status: str
    data: dict[str, Any]
    error: str | None = None

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return bool(
            self.status
        )

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "ready": self.ready(),
        }
