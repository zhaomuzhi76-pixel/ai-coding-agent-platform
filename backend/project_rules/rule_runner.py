"""规则执行器：跑所有规则，产出 Report。

Responsibility:
    - 按 rules.yaml 顺序执行所有 checker
    - 单规则失败不影响其它
Not Responsible:
    - 加载规则（loader）
    - 实现检查逻辑（checks/*）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import time

from .rule_loader import load_rules
from .rule_registry import CheckerRegistry
from .rule_types import Report, Rule, RuleResult


def run_all(
    root_path: str,
    *,
    rules: list[Rule] | None = None,
    registry: CheckerRegistry | None = None,
) -> Report:
    actual_rules = rules if rules is not None else load_rules()
    # 工业级：叠加用户实时规则参数覆盖（sqlite 里的 rule_param）
    try:
        from backend.agent_learning.rule_overrides import apply_all
        actual_rules = apply_all(actual_rules, workspace=root_path)
    except Exception as e:
        swallow("project_rules.rule_runner:32", e)
    reg = registry if registry is not None else _default_registry()
    # 工业级：注册扩展 checker（idempotent）
    try:
        reg.register_extended()
    except Exception as e:
        swallow("project_rules.rule_runner:38", e)

    started = time.time()
    results: list[RuleResult] = []
    for rule in actual_rules:
        checker = reg.get(rule.id)
        if checker is None:
            results.append(RuleResult(
                rule_id=rule.id, passed=False,
                error="no checker registered",
            ))
            continue
        t0 = time.perf_counter()
        try:
            r = checker.run(root_path, rule)
            # 工业级：透传 severity（RuleResult 有该字段时）
            if hasattr(r, "severity") and not getattr(r, "severity", None):
                from dataclasses import replace
                r = replace(r, severity=rule.severity)
            r = RuleResult(
                rule_id=r.rule_id,
                passed=r.passed,
                findings=r.findings,
                duration_ms=(time.perf_counter() - t0) * 1000,
                error=r.error,
            )
        except Exception as exc:
            r = RuleResult(
                rule_id=rule.id, passed=False,
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        results.append(r)

    return Report(
        results=tuple(results),
        started_at=started,
        finished_at=time.time(),
    )


_registry_singleton: CheckerRegistry | None = None


def _default_registry() -> CheckerRegistry:
    global _registry_singleton
    if _registry_singleton is None:
        reg = CheckerRegistry()
        n = reg.discover_builtin()
        if n == 0:
            raise RuntimeError(
                "no checkers discovered in backend.project_rules.checks"
            )
        _registry_singleton = reg
    return _registry_singleton


def format_report(report: Report) -> list[str]:
    lines = ["", "═" * 60, "  项目规则检查", "═" * 60]
    for r in report.results:
        icon = "PASS" if r.passed else "FAIL"
        lines.append(
            f"  [{icon}] {r.rule_id:30s} ({r.duration_ms:.1f}ms)"
        )
        for f in r.findings[:10]:
            lines.append(f"         · {f}")
        if r.error:
            lines.append(f"         ⚠ {r.error}")
    lines += [
        "═" * 60,
        f"  总计: {report.passed}/{report.total}",
        f"  结果: {'全部通过' if report.failed == 0 else f'{report.failed} 失败'}",
        "═" * 60,
    ]
    return lines


__all__ = ["run_all", "format_report"]
