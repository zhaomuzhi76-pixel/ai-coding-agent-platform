"""Message: a translation entry with named placeholders."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Message:
    key: str
    text: str
    description: str = ""

    def render(self, **params: Any) -> str:
        if not params:
            return self.text
        try:
            return self.text.format(**params)
        except (KeyError, IndexError):
            return self.text

    def dump(self) -> Dict[str, Any]:
        return {"key": self.key, "text": self.text,
                "description": self.description}
