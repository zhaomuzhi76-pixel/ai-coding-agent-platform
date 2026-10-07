"""Health cache: 带 TTL 的健康状态缓存。"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from backend.providers.health.record import HealthRecord

DEFAULT_TTL_SECONDS = 30.0


class HealthCache:
    VERSION = "1.0"

    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must positive")
        self._ttl = ttl_seconds
        self._records: Dict[str, HealthRecord] = {}

    def get(self, provider: str) -> Optional[HealthRecord]:
        rec = self._records.get(provider)
        if rec is None:
            return None
        if time.time() - rec.checked_at > self._ttl:
            return None
        return rec

    def put(self, record: HealthRecord) -> None:
        self._records[record.provider] = record

    def update_on_success(self, provider: str, latency_ms: float) -> None:
        self._records[provider] = HealthRecord(
            provider=provider, status="healthy",
            latency_ms=latency_ms, consecutive_failures=0,
        )

    def update_on_failure(self, provider: str, error: str) -> HealthRecord:
        prev = self._records.get(provider)
        cf = (prev.consecutive_failures if prev else 0) + 1
        rec = HealthRecord(
            provider=provider, status="unhealthy",
            error=error[:200], consecutive_failures=cf,
        )
        self._records[provider] = rec
        return rec

    def all(self) -> List[HealthRecord]:
        return list(self._records.values())

    def snapshot(self) -> Dict[str, Dict]:
        return {p: r.to_dict() for p, r in self._records.items()}

    def invalidate(self, provider: str) -> None:
        self._records.pop(provider, None)

    def clear(self) -> None:
        self._records.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ttl_seconds": self._ttl,
            "cached_providers": list(self._records.keys()),
        }


__all__ = ["HealthCache", "DEFAULT_TTL_SECONDS"]
