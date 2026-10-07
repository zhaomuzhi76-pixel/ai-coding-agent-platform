"""工业级分析报告（不是错误列表）。

输出三层：
  1. 项目概览（文件/行/规则）
  2. 问题分类（严重/警告/信息）+ 影响面 + 建议
  3. 通过清单
"""
from __future__ import annotations

import re
from pathlib import Path

from backend.project_rules.rule_types import Report, RuleResult


# 每个 rule_id → 建议生成函数（接收 rule_args，动态渲染）
# 零硬编码：所有数字/阈值从 rule.args 读取
_ADVICE_FN = {
    "file_size_max_230":
        lambda a: (f"拆分超大文件；目标每个文件 ≤ "
                   f"{a.get('max_lines', 230)} 行"),
    "no_duplicate_responsibility":
        lambda a: (f"关注 [{int(a.get('high_similarity', 0.85)*100)}%+] "
                   f"的真重复；[疑似] 需人工确认；[通用名] 无需处理"),
    "no_exit":
        lambda a: "库内使用异常；进程入口点可加入白名单",
    "layer_purity":
        lambda a: "上层依赖下层；不允许反向/跨层依赖",
    "plugin_pattern":
        lambda a: "新能力通过插件 + 新增文件实现",
    "tmpfs_only":
        lambda a: "测试使用 /dev/shm 或 tmpfile()，不写磁盘",
    "style_reference":
        lambda a: "参考 codex / claude-code / aliyun / dify 工业级风格",
    "debt_ratchet":
        lambda a: "旧债不恶化；新文件须 ≤ 阈值",
}


def _advice_for(rule_id: str, rule_args: dict) -> str:
    """零硬编码：动态生成建议。"""
    fn = _ADVICE_FN.get(rule_id)
    if fn is None:
        return ""
    try:
        return fn(rule_args or {})
    except Exception:
        return ""


def classify(results: tuple[RuleResult, ...]) -> dict[str, list]:
    out: dict[str, list] = {"error": [], "warn": [], "info": []}
    for r in results:
        if r.passed:
            continue
        sev = getattr(r, "severity", "error") or "error"
        out.setdefault(sev, []).append(r)
    return out


def _impact(findings: tuple[str, ...]) -> str:
    """从 findings 里分析影响模块。"""
    mods: dict[str, int] = {}
    for f in findings:
        for m in re.findall(r"([\w./-]+/)", f):
            mods[m] = mods.get(m, 0) + 1
    top = sorted(mods.items(), key=lambda x: -x[1])[:3]
    if not top:
        return ""
    return " · 影响: " + ", ".join(f"{m}({n})" for m, n in top)


def _group_findings(findings: tuple[str, ...]) -> dict[str, list[str]]:
    """no_duplicate 特殊：分真重复/疑似/通用名。"""
    groups: dict[str, list[str]] = {"real": [], "suspect": [],
                                     "common": [], "other": []}
    for f in findings:
        if f.startswith("[疑似]"):
            groups["suspect"].append(f[6:].strip())
        elif f.startswith("[通用名]"):
            groups["common"].append(f[6:].strip())
        elif f.startswith("[") and "]" in f[:6]:
            groups["real"].append(f)
        else:
            groups["other"].append(f)
    return groups


def _render_one(sev: str, r: RuleResult,
                rule_args: dict | None = None) -> list[str]:
    mark = {"error": "❌", "warn": "⚠️ ", "info": "·"}.get(sev, "·")
    out: list[str] = [f"  {mark} [{r.rule_id}]"]
    advice = _advice_for(r.rule_id, rule_args or {})
    if advice:
        out.append(f"     💡 {advice}")

    if r.rule_id == "no_duplicate_responsibility":
        g = _group_findings(r.findings)
        if g["real"]:
            out.append(f"     ● 真重复（相似度 ≥ 85%）: {len(g['real'])} 条")
            for x in g["real"][:6]:
                out.append(f"        {x}")
        if g["suspect"]:
            out.append(f"     ○ 疑似（50-85%）: {len(g['suspect'])} 条")
            for x in g["suspect"][:3]:
                out.append(f"        {x}")
        if g["common"]:
            out.append(f"     · 通用名（不同职责）: {len(g['common'])} 条")
        return out

    # 常规：前 6 条 + 影响面
    for f in r.findings[:6]:
        out.append(f"        {f}")
    if len(r.findings) > 6:
        out.append(f"        ... 还有 {len(r.findings)-6} 条")
    impact = _impact(r.findings)
    if impact:
        out.append(f"     {impact}")
    return out


def render(report: Report, *, root: str, title: str = "",
           rule_args_map: dict | None = None) -> str:
    groups = classify(report.results)
    lines: list[str] = [
        "═" * 66,
        title or f"工业级项目分析 · {root}",
        "═" * 66,
        "",
        "【项目概览】",
        f"  · 检测规则: {report.total} 个 "
        f"({report.passed} 通过, {report.failed} 失败)",
        f"  · 耗时: {(report.finished_at - report.started_at)*1000:.0f}ms",
        "",
    ]

    total_issues = sum(len(groups[s]) for s in groups)
    if total_issues == 0:
        lines.append("✅ 全部通过 —— 未发现问题")
        return "\n".join(lines)

    args_map = rule_args_map or {}

    for sev, label in (("error", "严重问题"), ("warn", "警告"),
                       ("info", "信息")):
        items = groups.get(sev) or []
        if not items:
            continue
        lines.append(f"【{label} · {len(items)} 类】")
        for r in items:
            lines.extend(_render_one(
                sev, r, args_map.get(r.rule_id, {}),
            ))
        lines.append("")

    passed = [r.rule_id for r in report.results if r.passed]
    if passed:
        lines.append(f"【通过 · {len(passed)} 条】")
        lines.append("  ✓ " + "  ✓ ".join(passed))
    return "\n".join(lines)


__all__ = ["classify", "render"]
