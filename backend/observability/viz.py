"""Tiny text visualizations (no external deps, no disk writes)."""
from __future__ import annotations

from typing import List, Sequence

_SPARK_CHARS = "▁▂▃▄▅▆▇█"
_BAR_FULL = "█"
_BAR_HALF = "▌"


def sparkline(values: Sequence[float]) -> str:
    """Compact single-line trend."""
    if not values:
        return ""
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span <= 0:
        return _SPARK_CHARS[0] * len(values)
    out: List[str] = []
    for v in values:
        ratio = (v - lo) / span
        idx = min(len(_SPARK_CHARS) - 1, int(ratio * len(_SPARK_CHARS)))
        out.append(_SPARK_CHARS[idx])
    return "".join(out)


def bar_chart(
    items: Sequence[tuple], width: int = 40, show_value: bool = True,
) -> str:
    """Horizontal bar chart. items = [(label, value), ...]"""
    if not items:
        return "(empty)"
    max_label = max(len(str(label)) for label, _ in items)
    max_value = max(float(v) for _, v in items) or 1.0
    lines: List[str] = []
    for label, value in items:
        v = float(value)
        bar_len = int((v / max_value) * width)
        bar = _BAR_FULL * bar_len
        if show_value:
            lines.append(f"  {str(label):<{max_label}}  {bar} {v:.3f}")
        else:
            lines.append(f"  {str(label):<{max_label}}  {bar}")
    return "\n".join(lines)


def table(
    headers: Sequence[str], rows: Sequence[Sequence[str]],
) -> str:
    """ASCII table."""
    if not headers:
        return "(empty)"
    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i in range(min(cols, len(row))):
            widths[i] = max(widths[i], len(str(row[i])))
    sep = "  "
    head = sep.join(
        str(h).ljust(widths[i]) for i, h in enumerate(headers)
    )
    rule = sep.join("-" * widths[i] for i in range(cols))
    body: List[str] = []
    for row in rows:
        cells = [
            str(row[i] if i < len(row) else "").ljust(widths[i])
            for i in range(cols)
        ]
        body.append(sep.join(cells))
    return "\n".join(["  " + head, "  " + rule] + ["  " + b for b in body])


def histogram(
    values: Sequence[float], buckets: int = 10, width: int = 30,
) -> str:
    """Simple histogram."""
    if not values:
        return "(no data)"
    buckets = max(2, int(buckets))
    lo = min(values)
    hi = max(values)
    span = hi - lo or 1.0
    counts = [0] * buckets
    for v in values:
        idx = min(buckets - 1, int(((v - lo) / span) * buckets))
        counts[idx] += 1
    max_count = max(counts) or 1
    lines: List[str] = []
    step = span / buckets
    for i, c in enumerate(counts):
        left = lo + i * step
        right = left + step
        bar = _BAR_FULL * int((c / max_count) * width)
        lines.append(
            f"  [{left:>8.2f},{right:>8.2f})  {bar} {c}"
        )
    return "\n".join(lines)


def pct_gauge(pct: float, width: int = 30) -> str:
    """Progress gauge 0..100."""
    pct = max(0.0, min(100.0, float(pct)))
    filled = int((pct / 100.0) * width)
    half = _BAR_HALF if (pct / 100.0) * width - filled >= 0.5 else ""
    return f"[{_BAR_FULL * filled}{half}{' ' * (width - filled - len(half))}] {pct:.1f}%"


__all__ = ["sparkline", "bar_chart", "table", "histogram", "pct_gauge"]
