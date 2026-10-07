"""Locale: language tag + normalization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

ZH_CN = "zh-CN"
EN_US = "en-US"

SUPPORTED = (ZH_CN, EN_US)
DEFAULT_LOCALE = ZH_CN


@dataclass(frozen=True)
class Locale:
    tag: str
    language: str
    region: str = ""

    @classmethod
    def parse(cls, tag: str) -> "Locale":
        raw = (tag or "").strip().replace("_", "-")
        if not raw:
            return cls.parse(DEFAULT_LOCALE)
        parts = raw.split("-")
        lang = parts[0].lower()
        region = parts[1].upper() if len(parts) > 1 else ""
        return cls(tag=f"{lang}-{region}" if region else lang,
                   language=lang, region=region)

    def to_tag(self) -> str:
        return self.tag


def normalize(tag: str) -> str:
    """Normalize to our canonical form; fall back to default."""
    if not tag:
        return DEFAULT_LOCALE
    parsed = Locale.parse(tag)
    for s in SUPPORTED:
        if s.lower() == parsed.tag.lower():
            return s
    # 语言级兜底：zh-XX -> zh-CN；en-XX -> en-US
    if parsed.language == "zh":
        return ZH_CN
    if parsed.language == "en":
        return EN_US
    return DEFAULT_LOCALE


def pick_best(accept_language: Optional[str]) -> str:
    """Parse Accept-Language header (q-value) and pick best supported."""
    if not accept_language:
        return DEFAULT_LOCALE
    entries = []
    for piece in accept_language.split(","):
        piece = piece.strip()
        if not piece:
            continue
        tag, _, qpart = piece.partition(";")
        try:
            q = float(qpart.strip().split("=")[1]) if "=" in qpart else 1.0
        except (ValueError, IndexError):
            q = 1.0
        entries.append((q, tag.strip()))
    entries.sort(key=lambda x: -x[0])
    for _, tag in entries:
        candidate = normalize(tag)
        if candidate in SUPPORTED:
            return candidate
    return DEFAULT_LOCALE


__all__ = [
    "Locale", "ZH_CN", "EN_US", "SUPPORTED", "DEFAULT_LOCALE",
    "normalize", "pick_best",
]
