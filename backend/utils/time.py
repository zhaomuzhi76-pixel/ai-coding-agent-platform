from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


SHANGHAI_TZ = ZoneInfo(
    "Asia/Shanghai"
)


def now() -> datetime:
    """
    Return timezone-aware Shanghai datetime.

    Project standard:
        UTC+8
        Asia/Shanghai
    """
    return datetime.now(
        SHANGHAI_TZ
    )


def now_iso() -> str:
    """
    Return ISO8601 timestamp.
    """
    return now().isoformat()


def now_timestamp() -> float:
    """
    Return Unix timestamp.
    """
    return now().timestamp()


__all__ = [
    "SHANGHAI_TZ",
    "now",
    "now_iso",
    "now_timestamp",
]
