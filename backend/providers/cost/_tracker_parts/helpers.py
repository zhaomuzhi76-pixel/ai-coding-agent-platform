"""Top-level helpers of tracker.py."""
from ._header import Any, CallRecord, Dict, List, Optional, Tuple, _agg_bucket, _finalize, _percentile, annotations, defaultdict, is_local_provider, time

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
