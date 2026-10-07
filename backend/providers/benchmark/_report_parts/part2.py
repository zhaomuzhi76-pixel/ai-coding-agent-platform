"""Part 2 of report.py."""
from __future__ import annotations
from .part1 import (BenchmarkResult, _CATEGORY_LABEL, _LINE, _RATING_LABEL,)  # noqa
from .part1 import _bar  # noqa
from .part1 import _case_line  # noqa
from .part1 import analyze_strengths  # noqa
from .part1 import analyze_weaknesses  # noqa
from .part1 import avoid_scenarios  # noqa
from .part1 import recommend_scenarios  # noqa

def render_summary_line(result: BenchmarkResult) -> str:
    """单行摘要（列表页用）。"""
    return (
        f"{result.provider}/{result.model}  "
        f"{result.score:.1f}/100  {result.rating}  "
        f"{result.elapsed_sec}s"
    )

def render_text(result: BenchmarkResult) -> str:
    """完整文本报告（人类可读）。"""
    lines: list[str] = []

    # ── 头部 ──
    lines.append(_LINE)
    lines.append("  模型能力测试报告")
    lines.append(_LINE)
    lines.append(f"  Provider:  {result.provider}")
    lines.append(f"  Model:     {result.model}")
    from datetime import datetime
    ts = datetime.fromtimestamp(result.started_at).strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"  测试时间:  {ts}")
    lines.append(f"  耗时:      {result.elapsed_sec}s")
    if result.error:
        lines.append(f"  ⚠️  错误:   {result.error}")
    lines.append("")

    # ── 总分 ──
    lines.append(f"【总分】{result.score:.1f} / 100   评级 {_RATING_LABEL.get(result.rating, result.rating)}")
    lines.append(f"  {_bar(result.score, 20)}  ({result.score:.0f}%)")
    lines.append("")

    # ── 分类 ──
    if result.by_category:
        lines.append("【分类表现】")
        for cat in ("capability", "latency", "stability", "cost"):
            if cat not in result.by_category:
                continue
            s = result.by_category[cat]
            label = _CATEGORY_LABEL.get(cat, cat)
            lines.append(f"  {label:<12} {_bar(s)}  {s:.0f} / 100")
        lines.append("")

    # ── 用例明细 ──
    lines.append("【用例明细】")
    for c in result.cases:
        lines.append(_case_line(c))
    lines.append("")

    # ── 擅长 ──
    strengths = analyze_strengths(result)
    lines.append("【擅长能力】")
    if strengths:
        for s in strengths:
            lines.append(f"  ✅ {s}")
    else:
        lines.append("  （无明显突出能力）")
    lines.append("")

    # ── 不擅长 ──
    weaknesses = analyze_weaknesses(result)
    lines.append("【不擅长】")
    if weaknesses:
        for w in weaknesses:
            lines.append(f"  ⚠️  {w}")
    else:
        lines.append("  ✅ 无显著短板")
    lines.append("")

    # ── 推荐场景 ──
    lines.append("【推荐场景】")
    for s in recommend_scenarios(result):
        lines.append(f"  - {s}")
    lines.append("")

    # ── 不推荐场景 ──
    avoids = avoid_scenarios(result)
    if avoids:
        lines.append("【不推荐场景】")
        for s in avoids:
            lines.append(f"  - {s}")
        lines.append("")

    lines.append(_LINE)
    return "\n".join(lines)

__all__ = [
    "render_text",
    "render_summary_line",
    "analyze_strengths",
    "analyze_weaknesses",
    "recommend_scenarios",
    "avoid_scenarios",
]
