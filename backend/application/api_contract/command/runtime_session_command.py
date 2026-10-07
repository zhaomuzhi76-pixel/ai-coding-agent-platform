from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True,
)
class RuntimeSessionCommand:
    """
    Runtime Session command contract.
    """

    name: str
    arguments: dict[str, Any]

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return bool(
            self.name
        )

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "name": self.name,
            "arguments": self.arguments,
            "ready": self.ready(),
        }
