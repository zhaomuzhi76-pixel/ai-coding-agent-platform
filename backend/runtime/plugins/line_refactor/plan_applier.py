"""应用拆分计划：写盘 + 删除原文件（保留 .bak）。"""
from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

from backend.runtime.plugins.line_refactor.plan_models import ApplyReport

if TYPE_CHECKING:
    from backend.runtime.plugins.line_refactor.plan_models import (
        RefactorPlan,
        SplitPlan,
    )


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def apply_split(plan: SplitPlan, keep_backup: bool = True) -> ApplyReport:
    report = ApplyReport()
    if not plan.applicable:
        report.failed.append(f"{plan.source_path}: not applicable")
        return report
    try:
        os.makedirs(plan.package_dir, exist_ok=True)
        init_path = os.path.join(plan.package_dir, "__init__.py")
        _write(init_path, plan.init_source)
        report.written.append(init_path)
        for part in plan.parts:
            part_path = os.path.join(plan.package_dir, part.filename)
            _write(part_path, part.source)
            report.written.append(part_path)
        if keep_backup:
            backup = plan.source_path + ".bak"
            shutil.copy2(plan.source_path, backup)
            report.written.append(backup)
        os.remove(plan.source_path)
        report.removed.append(plan.source_path)
    except OSError as exc:
        report.failed.append(f"{plan.source_path}: {exc}")
    return report


def apply_plan(plan: RefactorPlan, keep_backup: bool = True) -> ApplyReport:
    combined = ApplyReport()
    for split in plan.applicable:
        r = apply_split(split, keep_backup=keep_backup)
        combined.written.extend(r.written)
        combined.removed.extend(r.removed)
        combined.failed.extend(r.failed)
    return combined
