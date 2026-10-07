"""渲染重构计划到文本。"""
from __future__ import annotations

from backend.runtime.plugins.line_refactor.plan_models import RefactorPlan


def render_plan(plan: RefactorPlan) -> str:
    lines = [plan.summary()]
    for s in plan.applicable:
        lines.append("")
        lines.append(f"--- {s.source_path} ---")
        lines.append(f"  package_dir: {s.package_dir}")
        lines.append(f"  parts: {len(s.parts)}")
        for p in s.parts:
            n = p.source.count("\n") + 1
            lines.append(
                f"    - {p.filename} ({n} lines, "
                f"exports={len(p.exported_names)})"
            )
    return "\n".join(lines)
