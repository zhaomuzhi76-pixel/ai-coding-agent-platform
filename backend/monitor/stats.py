"""统计聚合 —— 从调用记录算出 KPI / 趋势 / 分组"""
import time
from collections import defaultdict
from typing import Any, Dict, List

from .pricing import calc_cost
from .recorder import list_calls


def _bucket(ts: float, granularity: str) -> str:
    t = time.localtime(ts)
    if granularity == "hour":
        return time.strftime("%Y-%m-%d %H:00", t)
    return time.strftime("%Y-%m-%d", t)


def summary(hours: int = 24) -> Dict[str, Any]:
    since = time.time() - hours * 3600
    calls = list_calls(limit=100000, since=since)
    total = len(calls)
    if total == 0:
        return {
            "window_hours": hours, "total_calls": 0, "success_rate": 0.0,
            "avg_latency_ms": 0, "p95_latency_ms": 0,
            "total_tokens": 0, "total_cost_usd": 0.0,
            "online_calls": 0, "offline_calls": 0,
        }
    ok = [c for c in calls if c.get("success")]
    latencies = sorted(c.get("latency_ms", 0) for c in calls if c.get("latency_ms"))
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    total_cost = sum(
        calc_cost(c["model"], c["provider"],
                  c.get("prompt_tokens", 0), c.get("completion_tokens", 0))
        for c in calls
    )
    return {
        "window_hours": hours,
        "total_calls": total,
        "success_rate": round(len(ok) / total, 4),
        "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
        "p95_latency_ms": p95,
        "total_tokens": sum(c.get("total_tokens", 0) for c in calls),
        "total_cost_usd": round(total_cost, 4),
        "online_calls": sum(1 for c in calls if c.get("online")),
        "offline_calls": sum(1 for c in calls if not c.get("online")),
    }


def trend(hours: int = 24, granularity: str = "hour") -> List[Dict[str, Any]]:
    since = time.time() - hours * 3600
    calls = list_calls(limit=100000, since=since)
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "tokens": 0, "cost": 0.0, "latency_sum": 0}
    )
    for c in calls:
        key = _bucket(c.get("ts", 0), granularity)
        b = buckets[key]
        b["calls"] += 1
        b["tokens"] += c.get("total_tokens", 0)
        b["latency_sum"] += c.get("latency_ms", 0)
        b["cost"] += calc_cost(c["model"], c["provider"],
                               c.get("prompt_tokens", 0),
                               c.get("completion_tokens", 0))
    return [
        {"bucket": k, "calls": v["calls"], "tokens": v["tokens"],
         "cost": round(v["cost"], 4),
         "avg_latency_ms": int(v["latency_sum"] / v["calls"]) if v["calls"] else 0}
        for k, v in sorted(buckets.items())
    ]


def by_model(hours: int = 24) -> List[Dict[str, Any]]:
    since = time.time() - hours * 3600
    calls = list_calls(limit=100000, since=since)
    groups: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"provider": "", "calls": 0, "success": 0, "tokens": 0,
                 "cost": 0.0, "latency_sum": 0}
    )
    for c in calls:
        key = c.get("model", "?")
        g = groups[key]
        g["provider"] = c.get("provider", "")
        g["calls"] += 1
        if c.get("success"):
            g["success"] += 1
        g["tokens"] += c.get("total_tokens", 0)
        g["latency_sum"] += c.get("latency_ms", 0)
        g["cost"] += calc_cost(c["model"], c["provider"],
                               c.get("prompt_tokens", 0),
                               c.get("completion_tokens", 0))
    return [
        {
            "model": k, "provider": v["provider"], "calls": v["calls"],
            "success_rate": round(v["success"] / v["calls"], 4) if v["calls"] else 0,
            "tokens": v["tokens"], "cost_usd": round(v["cost"], 4),
            "avg_latency_ms": int(v["latency_sum"] / v["calls"]) if v["calls"] else 0,
        }
        for k, v in sorted(groups.items(), key=lambda x: -x[1]["calls"])
    ]


def by_provider(hours: int = 24) -> List[Dict[str, Any]]:
    since = time.time() - hours * 3600
    calls = list_calls(limit=100000, since=since)
    groups: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "tokens": 0, "cost": 0.0, "latency_sum": 0}
    )
    for c in calls:
        key = c.get("provider", "?")
        g = groups[key]
        g["calls"] += 1
        g["tokens"] += c.get("total_tokens", 0)
        g["latency_sum"] += c.get("latency_ms", 0)
        g["cost"] += calc_cost(c["model"], c["provider"],
                               c.get("prompt_tokens", 0),
                               c.get("completion_tokens", 0))
    return [
        {
            "provider": k, "calls": v["calls"], "tokens": v["tokens"],
            "cost_usd": round(v["cost"], 4),
            "avg_latency_ms": int(v["latency_sum"] / v["calls"]) if v["calls"] else 0,
        }
        for k, v in sorted(groups.items(), key=lambda x: -x[1]["calls"])
    ]
