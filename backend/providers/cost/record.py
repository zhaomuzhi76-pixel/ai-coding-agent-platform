"""Cost record: 单次 LLM 调用成本。"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Set

# 视为「本地」的 provider 名关键词（无成本）
_LOCAL_MARKERS: Set[str] = {"ollama", "local", "lmstudio", "vllm-local"}


def is_local_provider(provider: str) -> bool:
    p = (provider or "").lower()
    return any(m in p for m in _LOCAL_MARKERS)


@dataclass(frozen=True)
class CallRecord:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    role: str = ""
    success: bool = True
    error: str = ""
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    @property
    def is_local(self) -> bool:
        return is_local_provider(self.provider)

    @property
    def day_key(self) -> str:
        return time.strftime("%Y-%m-%d", time.localtime(self.created_at))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "provider": self.provider,
            "model": self.model,
            "role": self.role,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": round(self.cost, 6),
            "latency_ms": round(self.latency_ms, 2),
            "success": self.success,
            "error": self.error[:200],
            "is_local": self.is_local,
            "created_at": self.created_at,
        }


__all__ = ["CallRecord", "is_local_provider"]
