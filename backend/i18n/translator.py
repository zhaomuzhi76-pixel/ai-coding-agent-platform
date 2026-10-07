"""Translator: translation entry with fallback chain."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.i18n.catalog import MessageCatalog
from backend.i18n.locale import (
    DEFAULT_LOCALE, normalize,
)


class Translator:
    """Look up + render messages with per-call locale override."""

    VERSION = "1.0"
    MISSING_MARKER = "⟦missing:{key}⟧"

    def __init__(
        self, catalog: MessageCatalog,
        default_locale: str = DEFAULT_LOCALE,
    ) -> None:
        if catalog is None:
            raise ValueError("catalog required")
        self._catalog = catalog
        self._default = normalize(default_locale)

    def translate(
        self,
        key: str,
        locale: Optional[str] = None,
        **params: Any,
    ) -> str:
        tag = normalize(locale) if locale else self._default
        msg = self._catalog.get(tag, key)
        if msg is None:
            return self.MISSING_MARKER.format(key=key)
        return msg.render(**params)

    def has(self, key: str, locale: Optional[str] = None) -> bool:
        tag = normalize(locale) if locale else self._default
        return self._catalog.has(tag, key)

    def available_locales(self) -> list:
        return self._catalog.locales()

    def ready(self) -> bool:
        return self._catalog.ready()

    def dump(self) -> Dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "default_locale": self._default,
            "catalog": self._catalog.dump(),
        }


__all__ = ["Translator"]
