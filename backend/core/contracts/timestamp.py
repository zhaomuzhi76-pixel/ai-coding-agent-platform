from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


_SHANGHAI_TZ = ZoneInfo(
    "Asia/Shanghai"
)


def now_timestamp() -> str:
    return datetime.now(
        _SHANGHAI_TZ
    ).isoformat()


__all__ = [
    "now_timestamp",
]
