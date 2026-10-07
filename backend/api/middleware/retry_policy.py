"""Retry-After 动态计算（单一职责：根据队列状态算等待时间）。

公式：
    avg_handle_s = avg_wait_ms/1000   （无历史 → fallback）
    estimate     = queued * avg_handle_s / max_concurrent
    retry_after  = clamp(estimate, min, max)

零硬编码：所有边界值来自 cfg（MWConfig）。
"""
from __future__ import annotations


def compute(guard_snapshot: dict, cfg) -> int:
    """根据 guard 快照 + 配置动态算 Retry-After（秒）。"""
    queued = int(guard_snapshot.get("queued", 0))
    max_c = int(guard_snapshot.get("max_concurrent", 0)) or 1
    served = int(guard_snapshot.get("served", 0))
    avg_wait_ms = float(guard_snapshot.get("avg_wait_ms", 0.0))

    if served <= 0 or avg_wait_ms <= 0:
        avg_handle_s = float(cfg.retry_after_fallback_s)
    else:
        avg_handle_s = avg_wait_ms / 1000.0

    estimate = (queued * avg_handle_s) / max_c
    retry_after = int(estimate)
    if retry_after < cfg.retry_after_min_s:
        retry_after = cfg.retry_after_min_s
    if retry_after > cfg.retry_after_max_s:
        retry_after = cfg.retry_after_max_s
    return retry_after


def render_hint(cfg, retry_after: int) -> str:
    """用配置的模板渲染提示文本。"""
    try:
        return cfg.retry_hint_template.format(seconds=retry_after)
    except (KeyError, IndexError):
        return cfg.retry_hint_template


def build_503_payload(guard_snapshot: dict, cfg) -> tuple:
    """返回 (body_bytes, retry_after_s, hint)。供 install.py 复用。"""
    import json
    ra = compute(guard_snapshot, cfg)
    hint = render_hint(cfg, ra)
    body = json.dumps({
        "ok": False,
        "error": "server_busy",
        "hint": hint,
        "retry_after_s": ra,
    }).encode()
    return body, ra, hint
