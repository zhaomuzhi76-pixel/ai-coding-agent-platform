"""插件化模式检查：新能力必须落在独立文件里。

规则：
    - 每个 checks/*_check.py 必须导出 CHECKER 实例
    - checker 类必须有 rule_id 属性
"""
from __future__ import annotations

import importlib
import pkgutil

from backend.project_rules.rule_types import Rule, RuleResult


class PluginPatternChecker:
    rule_id = "plugin_pattern"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        findings: list[str] = []
        pkg = importlib.import_module("backend.project_rules.checks")
        for _, name, _ in pkgutil.iter_modules(pkg.__path__):
            if not name.endswith("_check"):
                continue
            mod = importlib.import_module(
                f"backend.project_rules.checks.{name}"
            )
            checker = getattr(mod, "CHECKER", None)
            if checker is None:
                findings.append(f"{name}: missing CHECKER")
                continue
            if not getattr(checker, "rule_id", ""):
                findings.append(f"{name}: CHECKER has no rule_id")
        return RuleResult(
            rule_id=rule.id,
            passed=not findings,
            findings=tuple(findings),
        )


CHECKER = PluginPatternChecker()
