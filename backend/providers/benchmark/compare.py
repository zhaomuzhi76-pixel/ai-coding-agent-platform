"""多模型对比报告生成器（L3）。"""
from __future__ import annotations
from typing import Iterable
from .evaluator import BenchmarkCaseResult
from .report import analyze_strengths
from .runner import BenchmarkResult

_LINE = "═" * 64
_CASE_ORDER = (
    "first_token", "full_latency", "success_rate",
    "json_follow", "tool_call", "chinese",
    "long_context", "reasoning", "cost_per_call", "consistency",
)
_CASE_LABEL = {
    "first_token": "首 token 延迟",
    "full_latency": "完整延迟",
    "success_rate": "成功率",
    "json_follow": "JSON 遵循",
    "tool_call": "工具调用",
    "chinese": "中文能力",
    "long_context": "长上下文",
    "reasoning": "推理能力",
    "cost_per_call": "单次成本",
    "consistency": "一致性",
}


def _cmap(r: BenchmarkResult) -> dict[str, BenchmarkCaseResult]:
    return {c.case_id: c for c in r.cases}


def _metric(c: BenchmarkCaseResult | None) -> str:
    if c is None:
        return "—"
    if c.case_id == "first_token":
        return f"{c.first_token_ms:.0f}ms" if c.first_token_ms > 0 else "—"
    if c.case_id == "full_latency":
        return f"{c.latency_ms / 1000:.2f}s" if c.latency_ms > 0 else "—"
    if c.case_id == "success_rate":
        return f"{c.successes}/{c.attempts}"
    if c.case_id == "cost_per_call":
        return "$0" if c.cost == 0 else f"${c.cost:.4f}"
    if c.case_id == "consistency":
        return f"{c.score * 100:.0f}"
    return f"{c.score * 100:.0f}"


def rank_models(results: Iterable[BenchmarkResult]) -> list[BenchmarkResult]:
    return sorted(list(results), key=lambda r: -r.score)


def build_compare_table(results: Iterable[BenchmarkResult]) -> list[dict]:
    rs = list(results)
    if not rs:
        return []
    rows: list[dict] = []
    rows.append({"metric": "__model__", "label": "模型",
                 "values": [f"{r.model} ({r.provider})" for r in rs]})
    rows.append({"metric": "score", "label": "总分",
                 "values": [f"{r.score:.1f}" for r in rs]})
    rows.append({"metric": "rating", "label": "评级",
                 "values": [r.rating for r in rs]})
    rows.append({"metric": "elapsed_sec", "label": "耗时",
                 "values": [f"{r.elapsed_sec:.1f}s" for r in rs]})
    for cid in _CASE_ORDER:
        label = _CASE_LABEL.get(cid, cid)
        vals = [_metric(_cmap(r).get(cid)) for r in rs]
        rows.append({"metric": cid, "label": label, "values": vals})
    return rows


def recommend_by_scenario(results: Iterable[BenchmarkResult]) -> dict[str, str]:
    rs = list(results)
    if not rs:
        return {}

    def best_by(cid: str) -> str:
        best_r = None
        best_v = None
        for r in rs:
            c = _cmap(r).get(cid)
            if c is None:
                continue
            if best_v is None or c.score > best_v:
                best_v = c.score
                best_r = r
        if best_r is None:
            return ""
        return f"{best_r.model} ({best_r.provider})"

    out = {
        "中文对话": best_by("chinese"),
        "代码/推理": best_by("reasoning"),
        "Agent 编排": best_by("tool_call"),
        "结构化输出": best_by("json_follow"),
        "长文档分析": best_by("long_context"),
    }
    return {k: v for k, v in out.items() if v}


def render_compare_text(results: Iterable[BenchmarkResult]) -> str:
    rs = list(results)
    lines: list[str] = []
    lines.append(_LINE)
    lines.append("  模型能力对比报告")
    lines.append(_LINE)
    lines.append(f"  模型数：{len(rs)}")
    if rs:
        from datetime import datetime
        ts = min(r.started_at for r in rs)
        lines.append(f"  最早测试：{datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("【总分排名】")
    for i, r in enumerate(rank_models(rs), 1):
        lines.append(f"  {i}. {r.model:<24} {r.score:>5.1f}  {r.rating}")
    lines.append("")
    lines.append("【分项对比】")
    table = build_compare_table(rs)
    if not table:
        lines.append("  （无数据）")
    else:
        label_w = max(len(row["label"]) for row in table)
        col_w = max(max(len(str(v)) for v in row["values"]) for row in table)
        header = "  " + "指标".ljust(label_w) + " | " + " | ".join(
            f"模型{i+1}".ljust(col_w) for i in range(len(rs))
        )
        lines.append(header)
        lines.append("  " + "-" * (len(header) - 2))
        for row in table:
            cells = " | ".join(str(v).ljust(col_w) for v in row["values"])
            lines.append("  " + row["label"].ljust(label_w) + " | " + cells)
    lines.append("")
    lines.append("【各自擅长】")
    for r in rs:
        strengths = analyze_strengths(r)
        if strengths:
            lines.append(f"  {r.model}：")
            for s in strengths:
                lines.append(f"    ✅ {s}")
        else:
            lines.append(f"  {r.model}：（无明显突出）")
    lines.append("")
    lines.append("【场景推荐】")
    scenario = recommend_by_scenario(rs)
    if scenario:
        for s, m in scenario.items():
            lines.append(f"  {s:<12} → {m}")
    else:
        lines.append("  （数据不足）")
    lines.append("")
    lines.append(_LINE)
    return "\n".join(lines)


def render_compare_markdown(results: Iterable[BenchmarkResult]) -> str:
    rs = list(results)
    lines: list[str] = []
    lines.append("# 模型能力对比报告")
    lines.append("")
    lines.append(f"**模型数**：{len(rs)}")
    if rs:
        from datetime import datetime
        ts = min(r.started_at for r in rs)
        lines.append(f"**最早测试**：{datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 总分排名")
    lines.append("")
    lines.append("| 排名 | 模型 | Provider | 总分 | 评级 | 耗时 |")
    lines.append("|------|------|----------|------|------|------|")
    for i, r in enumerate(rank_models(rs), 1):
        lines.append(
            f"| {i} | {r.model} | {r.provider} | {r.score:.1f} | {r.rating} | {r.elapsed_sec:.1f}s |"
        )
    lines.append("")
    lines.append("## 分项对比")
    lines.append("")
    table = build_compare_table(rs)
    if table:
        header = "| 指标 |" + "|".join(f" {r.model} " for r in rs) + "|"
        sep = "|------|" + "|".join("------" for _ in rs) + "|"
        lines.append(header)
        lines.append(sep)
        for row in table:
            if row["metric"] == "__model__":
                continue
            cells = "|".join(f" {v} " for v in row["values"])
            lines.append(f"| {row['label']} |{cells}|")
    lines.append("")
    lines.append("## 各自擅长")
    lines.append("")
    for r in rs:
        strengths = analyze_strengths(r)
        lines.append(f"### {r.model} ({r.provider})")
        if strengths:
            for s in strengths:
                lines.append(f"- ✅ {s}")
        else:
            lines.append("- （无明显突出）")
        lines.append("")
    lines.append("## 场景推荐")
    lines.append("")
    scenario = recommend_by_scenario(rs)
    if scenario:
        lines.append("| 场景 | 推荐模型 |")
        lines.append("|------|----------|")
        for s, m in scenario.items():
            lines.append(f"| {s} | {m} |")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "rank_models",
    "build_compare_table",
    "recommend_by_scenario",
    "render_compare_text",
    "render_compare_markdown",
]
