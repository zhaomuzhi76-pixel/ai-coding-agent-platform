"""Locale detection from request metadata."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.i18n.locale import (
    DEFAULT_LOCALE, normalize, pick_best,
)

HEADER_KEYS = (
    "accept-language",
    "Accept-Language",
    "x-locale",
    "X-Locale",
)


def detect_from_headers(
    headers: Optional[Dict[str, Any]],
) -> str:
    if not headers:
        return DEFAULT_LOCALE
    for key in HEADER_KEYS:
        value = headers.get(key)
        if not value:
            continue
        if key.lower() == "accept-language":
            return pick_best(str(value))
        return normalize(str(value))
    return DEFAULT_LOCALE


def detect_from_query(
    query: Optional[Dict[str, Any]],
) -> str:
    if not query:
        return DEFAULT_LOCALE
    for key in ("locale", "lang", "language"):
        value = query.get(key)
        if value:
            return normalize(str(value))
    return DEFAULT_LOCALE


def detect(
    headers: Optional[Dict[str, Any]] = None,
    query: Optional[Dict[str, Any]] = None,
) -> str:
    """Query > header > default."""
    from_query = detect_from_query(query)
    if from_query != DEFAULT_LOCALE:
        return from_query
    return detect_from_headers(headers)


__all__ = ["detect", "detect_from_headers", "detect_from_query"]
