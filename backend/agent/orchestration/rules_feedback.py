"""规则校验反馈契约（纯数据 + 渲染）。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RulesViolation:
    rule_id: str
    file: str
    message: str

    def to_line(self) -> str:
        return f"[{self.rule_id}] {self.file}: {self.message}"


@dataclass
class RulesFeedback:
    ok: bool
    violations: list[RulesViolation] = field(default_factory=list)
    checked_rules: int = 0
    #: 全局 require 规则（如 logger），作为"禁用什么 → 用什么"的替代提示
    substitutes: list[str] = field(default_factory=list)

    def to_prompt(self, max_n: int = 8) -> str:
        if self.ok:
            return ""
        lines = ["[Project rules FAILED — MUST fix before retry]"]
        for v in self.violations[:max_n]:
            lines.append(f"  - {v.to_line()}")
        if len(self.violations) > max_n:
            lines.append(f"  ... 还有 {len(self.violations)-max_n} 条")
        if self.substitutes:
            lines.append("")
            lines.append("用户全局规则要求使用以下替代方案：")
            for s in self.substitutes[:5]:
                lines.append(f"  → {s}")
        lines.append("")
        lines.append("CRITICAL: 项目规则优先于任务描述。")
        lines.append("  · 若任务要求与规则冲突（如任务说'用 print'"
                     "但规则禁止），必须按规则改用替代方案。")
        lines.append("  · 禁止输出任何被 forbid 的符号。")
        lines.append("")
        lines.append("Fix the above rule violations and retry.")
        return "\n".join(lines)


__all__ = ["RulesViolation", "RulesFeedback"]
