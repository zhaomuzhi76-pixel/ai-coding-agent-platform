"""重构编排器。"""
from __future__ import annotations

from typing import List

from backend.runtime.plugins.line_refactor.module_splitter import build_split_plan
from backend.runtime.plugins.line_refactor.plan_applier import apply_plan
from backend.runtime.plugins.line_refactor.plan_models import (
    ApplyReport,
    RefactorPlan,
    SplitPlan,
)
from backend.runtime.plugins.line_refactor.plan_renderer import render_plan
from backend.runtime.plugins.line_refactor.source_scanner import find_oversized

DEFAULT_HARD = 230
DEFAULT_SOFT = 180


class RefactorRunner:
    def __init__(self, hard: int = DEFAULT_HARD, soft: int = DEFAULT_SOFT) -> None:
        self._hard = hard
        self._soft = soft

    def plan(self, root: str) -> RefactorPlan:
        splits: List[SplitPlan] = []
        for path, _n in find_oversized(root, self._hard):
            splits.append(build_split_plan(path, soft=self._soft))
        return RefactorPlan(splits=splits, hard_limit=self._hard, soft_limit=self._soft)

    def render(self, root: str) -> str:
        return render_plan(self.plan(root))

    def apply(self, root: str, keep_backup: bool = True) -> ApplyReport:
        return apply_plan(self.plan(root), keep_backup=keep_backup)
