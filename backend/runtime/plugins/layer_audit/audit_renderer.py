"""Layer Audit 渲染。"""
from __future__ import annotations

from typing import List

from backend.runtime.plugins.layer_audit.audit_models import (
    AuditReport,
    FileProfile,
    Unit,
)


def _render_unit(u: Unit, indent: str = "    ") -> List[str]:
    lines = [f"{indent}[{u.kind}] {u.name} ({u.lines} lines)"]
    if u.kind == "class" and u.methods:
        for m, ml in zip(u.methods, u.method_lines):
            lines.append(f"{indent}    - {m}: {ml}")
    return lines


def _render_file(f: FileProfile) -> List[str]:
    lines = [f"### {f.rel_path}  ({f.lines} lines)"]
    for u in f.units:
        lines.extend(_render_unit(u))
    return lines


def render_report(report: AuditReport) -> str:
    out: List[str] = ["=== Layer Audit ==="]
    out.append(f"root={report.root}")
    out.append(f"files={len(report.files)} total_lines={report.total_lines}")
    out.append("")

    out.append(f"--- Oversized (>{230}) ---")
    if not report.oversized:
        out.append("  (none)")
    for f in report.oversized:
        out.append(f"  [OVER] {f.rel_path} ({f.lines})")
    out.append("")

    out.append("--- Duplicate Class Names ---")
    if not report.duplicate_classes:
        out.append("  (none)")
    for h in report.duplicate_classes:
        out.append(f"  {h.name} in {h.files}")
    out.append("")

    out.append("--- Duplicate Function Names ---")
    if not report.duplicate_functions:
        out.append("  (none)")
    for h in report.duplicate_functions:
        out.append(f"  {h.name} in {h.files}")
    out.append("")

    out.append("--- Internal Import Edges ---")
    if not report.internal_import_edges:
        out.append("  (none)")
    for src, dst in report.internal_import_edges:
        out.append(f"  {src} -> {dst}")
    out.append("")

    out.append("--- File Profiles ---")
    for f in sorted(report.files, key=lambda x: -x.lines):
        out.extend(_render_file(f))
        out.append("")
    return "\n".join(out)
