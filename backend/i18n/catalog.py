"""MessageCatalog: per-locale message table."""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.i18n.locale import (
    DEFAULT_LOCALE, SUPPORTED, normalize,
)
from backend.i18n.message import Message


class MessageCatalog:
    """Register messages per locale; lookup by key."""

    VERSION = "1.0"

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Message]] = {}

    def register(self, locale: str, message: Message) -> None:
        tag = normalize(locale)
        if not message.key.strip():
            raise ValueError("message.key required")
        self._data.setdefault(tag, {})[message.key] = message

    def register_many(
        self, locale: str, messages: List[Message],
    ) -> None:
        for m in messages:
            self.register(locale, m)

    def get(self, locale: str, key: str) -> Optional[Message]:
        tag = normalize(locale)
        msg = self._data.get(tag, {}).get(key)
        if msg is not None:
            return msg
        if tag != DEFAULT_LOCALE:
            return self._data.get(DEFAULT_LOCALE, {}).get(key)
        return None

    def has(self, locale: str, key: str) -> bool:
        return self.get(locale, key) is not None

    def locales(self) -> List[str]:
        return sorted(self._data.keys())

    def keys(self, locale: str) -> List[str]:
        tag = normalize(locale)
        return sorted(self._data.get(tag, {}).keys())

    def missing(self, locale: str, key: str) -> List[str]:
        """Return locales that don't have this key (audit helper)."""
        return [loc for loc in self.locales() if not self.has(loc, key)]

    def ready(self) -> bool:
        return bool(self._data)

    def dump(self) -> Dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "locales": self.locales(),
            "counts": {k: len(v) for k, v in self._data.items()},
            "supported": list(SUPPORTED),
        }


__all__ = ["MessageCatalog"]
