"""standards 独有审计（唯一入口是 project_rules.cli）。

只保留 project_rules 未覆盖的能力：
  · no_exit     库禁 exit
  · style       codex/claude/aliyun/dify 参考（warn）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.quality.standards.checks_basic import check_no_exit
from backend.quality.standards.checks_style import run_style
from backend.quality.standards.contracts import LayerReport


def run_audit(layer: str, as_json: bool = False) -> int:
    root = Path(layer)
    if not root.is_dir():
        print(f"❌ 目录不存在: {layer}", file=sys.stderr)
        return 2

    files = sorted(p for p in root.rglob("*.py"))
    report = LayerReport(layer=layer, files_scanned=len(files))
    for f in files:
        rel = (str(f.relative_to(root.parent))
               if f.is_relative_to(root.parent) else str(f))
        report.add(check_no_exit(f, rel))
        for r in run_style(f, rel):
            report.add(r)

    if as_json:
        print(json.dumps(report.summary(), ensure_ascii=False, indent=2))
    else:
        _render(report)
    return 0 if report.ok else 1


def _render(r: LayerReport) -> None:
    print("=" * 60)
    print(f"standards 独有检查 · {r.layer}")
    print("=" * 60)
    print(f"扫描: {r.files_scanned} 文件 · 检查: {len(r.results)} 项")
    by_rule: dict[str, list] = {}
    for x in r.results:
        by_rule.setdefault(x.rule_id, []).append(x)
    for rid in sorted(by_rule):
        items = by_rule[rid]
        fails = [x for x in items if not x.ok]
        mark = "✅" if not fails else "⚠️"
        print(f"  [{mark}] {rid:14} pass={len(items)-len(fails)} fail={len(fails)}")
    if r.errors:
        print(f"❌ {len(r.errors)} 错误")


__all__ = ["run_audit"]
