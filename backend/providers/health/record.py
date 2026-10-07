"""Health record: provider 健康状态。"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class HealthRecord:
    provider: str
    status: str
    latency_ms: float = 0.0
    error: str = ""
    checked_at: float = field(default_factory=time.time)
    consecutive_failures: int = 0

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
            "checked_at": self.checked_at,
            "consecutive_failures": self.consecutive_failures,
        }


__all__ = ["HealthRecord"]
