"""Part 1 of report.py."""
from __future__ import annotations

from typing import Iterable

from ..evaluator import BenchmarkCaseResult

from ..runner import BenchmarkResult

_LINE = "═" * 64

_BAR_WIDTH = 10

_CATEGORY_LABEL = {
    "latency": "延迟",
    "stability": "稳定性",
    "capability": "能力",
    "cost": "成本",
}

_RATING_LABEL = {
    "A+": "A+ (卓越)",
    "A":  "A  (优秀)",
    "B+": "B+ (良好)",
    "B":  "B  (合格)",
    "C":  "C  (及格)",
    "D":  "D  (不及格)",
}

def _bar(score_pct: float, width: int = _BAR_WIDTH) -> str:
    """0~100 → █████░░░░░ 形式。"""
    filled = max(0, min(width, round(score_pct / 100.0 * width)))
    return "█" * filled + "░" * (width - filled)

def _cmap(result: BenchmarkResult) -> dict[str, BenchmarkCaseResult]:
    return {c.case_id: c for c in result.cases}

def _case_line(c: BenchmarkCaseResult) -> str:
    """单行渲染一个用例。"""
    mark = "✅" if c.passed else "❌"
    # 指标摘要
    metric = ""
    if c.case_id == "first_token":
        metric = f"{c.first_token_ms:.0f}ms"
    elif c.case_id == "full_latency":
        metric = f"{c.latency_ms / 1000:.2f}s"
    elif c.case_id == "success_rate":
        metric = f"{c.successes}/{c.attempts}"
    elif c.case_id == "cost_per_call":
        metric = f"${c.cost:.4f}"
    elif c.case_id == "consistency":
        metric = f"方差 {'低' if c.score >= 0.9 else '高'}"
    else:
        metric = c.note.split("|")[0].strip() if c.note else ("通过" if c.passed else "失败")
    return f"  {mark} {c.name:<16} {metric:<24} {c.score * 100:>5.1f}"

def analyze_strengths(result: BenchmarkResult) -> list[str]:
    """返回擅长能力描述列表（基于评分规则）。"""
    cm = _cmap(result)
    out: list[str] = []

    zh = cm.get("chinese")
    if zh and zh.score >= 0.9:
        out.append("中文对话 / 内容生成")

    js = cm.get("json_follow")
    if js and js.score >= 0.9:
        out.append("结构化输出（JSON）")

    tc = cm.get("tool_call")
    if tc and tc.score >= 0.9:
        out.append("工具调用 / Agent 编排")

    rs = cm.get("reasoning")
    if rs and rs.score >= 0.9:
        out.append("逻辑推理")

    lc = cm.get("long_context")
    if lc and lc.passed:
        out.append("长文档 / 长上下文处理")

    ft = cm.get("first_token")
    if ft and ft.passed and ft.first_token_ms > 0 and ft.first_token_ms < 500:
        out.append("低延迟交互（首 token < 500ms）")

    sr = cm.get("success_rate")
    if sr and sr.score >= 0.95:
        out.append("高稳定性调用")

    cost = cm.get("cost_per_call")
    if cost and cost.cost == 0.0:
        out.append("零成本（本地部署）")

    cons = cm.get("consistency")
    if cons and cons.score >= 0.9:
        out.append("高一致性（多次输出稳定）")

    return out

def analyze_weaknesses(result: BenchmarkResult) -> list[str]:
    """返回不擅长能力（评分 < 0.7 或 failed）。"""
    out: list[str] = []
    for c in result.cases:
        if c.passed and c.score >= 0.7:
            continue
        reason = c.note.split("|")[0].strip() if c.note else "表现弱"
        if c.error:
            reason = c.error[:60]
        out.append(f"{c.name}（{reason}）")
    return out

def recommend_scenarios(result: BenchmarkResult) -> list[str]:
    """基于能力组合推荐场景。"""
    cm = _cmap(result)
    out: list[str] = []

    zh = cm.get("chinese")
    js = cm.get("json_follow")
    tc = cm.get("tool_call")
    rs = cm.get("reasoning")
    lc = cm.get("long_context")
    cost = cm.get("cost_per_call")
    sr = cm.get("success_rate")

    if zh and zh.score >= 0.8:
        out.append("中文内容生成 / 摘要 / 翻译")
    if js and js.score >= 0.8:
        out.append("API 集成 / 结构化数据抽取")
    if tc and tc.score >= 0.8:
        out.append("Agent 编排 / 多步工具链")
    if rs and rs.score >= 0.8:
        out.append("代码生成 / 复杂推理任务")
    if lc and lc.passed:
        out.append("长文档分析 / 知识库问答")
    if cost and cost.cost == 0.0 and sr and sr.score >= 0.9:
        out.append("高并发批处理（零成本 + 高稳定）")
    if not out:
        out.append("（通用场景，无突出优势）")
    return out

def avoid_scenarios(result: BenchmarkResult) -> list[str]:
    """基于弱点回避场景。"""
    cm = _cmap(result)
    out: list[str] = []

    tc = cm.get("tool_call")
    if tc and tc.score < 0.7:
        out.append("复杂 Agent 编排（工具调用弱）")

    rs = cm.get("reasoning")
    if rs and rs.score < 0.7:
        out.append("高精度代码修改 / 多步推理")

    js = cm.get("json_follow")
    if js and js.score < 0.7:
        out.append("严格 JSON 输出的 API 集成")

    zh = cm.get("chinese")
    if zh and zh.score < 0.7:
        out.append("中文用户对话")

    lc = cm.get("long_context")
    if lc and not lc.passed:
        out.append("长上下文任务")

    cons = cm.get("consistency")
    if cons and cons.score < 0.7:
        out.append("需要严格复现的任务")

    return out
