"""审查编排：生成配置 → 调 project_rules → 分级报告。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from pathlib import Path

from backend.quality.reviewer.auto_config import build_rules
from backend.quality.reviewer.reporter import render


def review(root: str, *, as_json: bool = False) -> int:
    from backend.project_rules.rule_registry import CheckerRegistry
    from backend.project_rules.rule_runner import run_all

    root_p = Path(root).resolve()
    if not root_p.is_dir():
        print(f"❌ 目录不存在: {root}")
        return 2

    rules = build_rules(root_p)
    # 提前应用用户参数覆盖（与 run_all 内一致，且 args_map 也用它）
    try:
        from backend.agent_learning.rule_overrides import apply_all
        rules = apply_all(rules, workspace=str(root_p))
    except Exception as e:
        swallow("quality.reviewer.runner:26", e)

    reg = CheckerRegistry()
    reg.discover_builtin()
    try:
        reg.register_extended()
    except Exception as e:
        swallow("quality.reviewer.runner:33", e)

    report = run_all(str(root_p), rules=rules, registry=reg)
    if as_json:
        import json
        print(json.dumps({
            "root": str(root_p),
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "results": [
                {"rule_id": r.rule_id, "passed": r.passed,
                 "findings": list(r.findings),
                 "error": r.error,
                 "severity": getattr(r, "severity", "error")}
                for r in report.results
            ],
        }, ensure_ascii=False, indent=2))
    else:
        args_map = {r.id: dict(r.args or {}) for r in rules}
        print(render(report, root=str(root_p),
                     title=f"工业级审查 · {root_p}",
                     rule_args_map=args_map))
    return 0 if report.failed == 0 else 1


__all__ = ["review"]
