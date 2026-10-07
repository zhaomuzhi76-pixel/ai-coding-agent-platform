"""Line Refactor 插件入口：只接线，不重复实现核心逻辑。"""
from __future__ import annotations

from backend.runtime.plugins.line_refactor.plan_models import (
    ApplyReport,
    RefactorPlan,
)
from backend.runtime.plugins.line_refactor.refactor_runner import RefactorRunner


class LineRefactorPlugin:
    name = "line_refactor"
    version = "1.1.0"

    def __init__(self, hard: int = 230, soft: int = 180) -> None:
        self._runner = RefactorRunner(hard=hard, soft=soft)
        self._hard = hard

    def plan(self, root: str) -> RefactorPlan:
        return self._runner.plan(root)

    def render_plan(self, root: str) -> str:
        return self._runner.render(root)

    def apply(self, root: str, keep_backup: bool = True) -> ApplyReport:
        return self._runner.apply(root, keep_backup=keep_backup)

    def diagnose(self, root: str) -> str:
        from backend.runtime.plugins.line_refactor.oversize_diagnoser import diagnose
        from backend.runtime.plugins.line_refactor.source_scanner import find_oversized
        out = []
        for path, _n in find_oversized(root, self._hard):
            out.append(diagnose(path).summary())
            out.append("")
        return "\n".join(out)
