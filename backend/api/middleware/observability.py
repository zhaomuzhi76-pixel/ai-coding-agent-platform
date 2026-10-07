"""观测聚合（中间件层）。

职责：单一（汇总 guard + cache 快照）。
不做：限流、缓存、路由。
"""
from __future__ import annotations


def aggregate(guard=None, cache=None) -> dict:
    """返回 {concurrency: ..., cache: ...}（缺省则不含）。"""
    out = {}
    if guard is not None and hasattr(guard, "snapshot"):
        out["concurrency"] = guard.snapshot()
    if cache is not None and hasattr(cache, "snapshot"):
        out["cache"] = cache.snapshot()
    return out
