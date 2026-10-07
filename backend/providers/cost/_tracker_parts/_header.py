"""CostTracker: 聚合 provider × model × role × 时间 的调用统计。

- 本地 LLM（ollama 等）：只统计次数 / 延迟，无成本
- 线上 LLM（dashscope / deepseek / anthropic / openai）：含成本
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from backend.providers.cost.record import (
    CallRecord,
    is_local_provider,
)


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    pct = max(0.0, min(100.0, pct))
    idx = int(round((pct / 100.0) * (len(sorted_values) - 1)))
    return round(sorted_values[idx], 2)


def _agg_bucket() -> Dict[str, Any]:
    return {
        "calls": 0,
        "success": 0,
        "errors": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0,
        "_latencies": [],
    }


def _finalize(bucket: Dict[str, Any]) -> Dict[str, Any]:
    lat = sorted(bucket.pop("_latencies", []))
    bucket["latency_p50"] = _percentile(lat, 50)
    bucket["latency_p95"] = _percentile(lat, 95)
    bucket["latency_max"] = round(lat[-1], 2) if lat else 0.0
    bucket["latency_avg"] = (
        round(sum(lat) / len(lat), 2) if lat else 0.0
    )
    bucket["cost"] = round(bucket["cost"], 6)
    return bucket
