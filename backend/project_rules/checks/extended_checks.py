"""扩展检查器：把 standards/debt/frontend 的独有能力注册为 project_rules 插件。

工业级：唯一入口是 project_rules.cli，本插件桥接独有能力。
不重复职责：仅编排，不重写检查逻辑。

注册的 3 个 Checker：
  · no_exit               ← standards.checks_basic
  · style_reference       ← standards.checks_style（codex/claude/aliyun/dify）
  · debt_ratchet          ← debt.ratchet（旧债不恶化）
"""
from __future__ import annotations

from pathlib import Path

from backend.project_rules.rule_types import (
    Rule, RuleResult,
)


# ─────────────────────────────────────────────────
# Checker 1: no_exit（standards 独有）
# ─────────────────────────────────────────────────

class NoExitChecker:
    rule_id = "no_exit"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        from backend.quality.standards.checks_basic import check_no_exit
        from backend.project_rules.discovery import should_skip
        root = Path(root_path)
        findings: list[str] = []
        for p in root.rglob("*.py"):
            if should_skip(p):
                continue
            if p.name.endswith((".bak", ".bak2", ".bak_dedup")):
                continue
            rel = p.relative_to(root).as_posix() \
                if p.is_relative_to(root) else str(p)
            r = check_no_exit(p, rel)
            if not r.ok:
                findings.append(f"{rel}: {r.message}")
        return RuleResult(
            rule_id=self.rule_id,
            passed=len(findings) == 0,
            findings=tuple(findings[:20]),
        )


# ─────────────────────────────────────────────────
# Checker 2: style_reference（standards 独有 · warn 级）
# ─────────────────────────────────────────────────

class StyleReferenceChecker:
    rule_id = "style_reference"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        from backend.quality.standards.checks_style import run_style
        root = Path(root_path)
        findings: list[str] = []
        scanned = 0
        for p in root.rglob("*.py"):
            if "__pycache__" in str(p):
                continue
            scanned += 1
            rel = p.relative_to(root).as_posix() \
                if p.is_relative_to(root) else str(p)
            for r in run_style(p, rel):
                if not r.ok and r.severity == "error":
                    findings.append(f"{rel}: {r.rule_id} {r.message}")
        return RuleResult(
            rule_id=self.rule_id,
            passed=len(findings) == 0,
            findings=tuple(findings[:20]),
        )


# ─────────────────────────────────────────────────
# Checker 3: debt_ratchet（debt 独有）
# ─────────────────────────────────────────────────

class DebtRatchetChecker:
    rule_id = "debt_ratchet"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        try:
            from backend.quality.debt.baseline import load
            from backend.quality.debt.ratchet import check
        except ImportError:
            return RuleResult(
                rule_id=self.rule_id, passed=True,
                findings=("(debt 模块未安装，跳过)",),
            )
        baseline_path = Path(rule.args.get("baseline_path",
                                           ".layer-review/debt-baseline.json"))
        bl = load(baseline_path)
        if not bl.entries:
            return RuleResult(
                rule_id=self.rule_id, passed=True,
                findings=("(no baseline)",),
            )
        rt = check(Path(root_path), bl)
        findings: list[str] = []
        for p, n in rt.new_violations[:10]:
            findings.append(f"NEW: {p} ({n} lines)")
        for p, old, new in rt.worsened[:10]:
            findings.append(f"WORSENED: {p} {old}→{new} lines")
        return RuleResult(
            rule_id=self.rule_id,
            passed=rt.ok,
            findings=tuple(findings),
        )


# ─────────────────────────────────────────────────
# 插件自动发现入口
# ─────────────────────────────────────────────────

CHECKER = NoExitChecker()      # 兼容旧 discover_builtin 单一 CHECKER 协议

CHECKERS = (
    NoExitChecker(),
    StyleReferenceChecker(),
    DebtRatchetChecker(),
)


def register_all(registry) -> int:
    """批量注册到 CheckerRegistry（新入口）。"""
    n = 0
    for c in CHECKERS:
        try:
            registry.register(c)
            n += 1
        except ValueError:
            pass   # already registered
    return n


__all__ = [
    "NoExitChecker", "StyleReferenceChecker", "DebtRatchetChecker",
    "CHECKER", "CHECKERS", "register_all",
]
