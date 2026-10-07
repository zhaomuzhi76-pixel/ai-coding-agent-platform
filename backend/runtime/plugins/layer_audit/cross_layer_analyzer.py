"""跨层审查：职责重复、命名伪装、引用热点。"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple

from backend.runtime.plugins.layer_audit.audit_models import (
    AuditReport,
    FileProfile,
    Unit,
)


_NORMALIZE_SUFFIXES = (
    "_value", "_values", "_context", "_context_value",
    "_required", "_required_value", "_required_context_value",
)


def _normalize_name(name: str) -> str:
    """归一化方法名，识别改名伪装的同职责函数。"""
    n = name.strip().lstrip("_")
    for suf in _NORMALIZE_SUFFIXES:
        if n.endswith(suf):
            return "required_value"
    return n


def find_disguised_duplicates(files: List[FileProfile]) -> List[Tuple]:
    """找出改名伪装但同职责的方法/函数。"""
    norm_to_locations: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for f in files:
        for u in f.units:
            if u.kind == "class":
                for m, ml in zip(u.methods, u.method_lines):
                    norm = _normalize_name(m)
                    norm_to_locations[f"{norm}::method"].append(
                        (f.rel_path, f"{u.name}.{m}", ml)
                    )
            elif u.kind in ("function", "async_function"):
                norm = _normalize_name(u.name)
                norm_to_locations[f"{norm}::func"].append(
                    (f.rel_path, u.name, u.lines)
                )
    hits = []
    for key, locs in norm_to_locations.items():
        unique_paths = {p for p, _, _ in locs}
        if len(unique_paths) > 1:
            hits.append((key, sorted(locs)))
    hits.sort(key=lambda x: (-len(x[1]), x[0]))
    return hits


def find_import_hotspots(files: List[FileProfile]) -> List[Tuple]:
    """找出被本层最多文件引用的外部模块。"""
    counter: Dict[str, Set[str]] = defaultdict(set)
    for f in files:
        for imp in f.imports:
            if imp.startswith("backend."):
                counter[imp].add(f.rel_path)
    ranked = sorted(counter.items(), key=lambda x: -len(x[1]))
    return [(mod, sorted(paths)) for mod, paths in ranked]


def render_cross_layer(report: AuditReport) -> str:
    out: List[str] = []
    out.append("=== Cross-Layer Analysis ===")
    out.append(f"files={len(report.files)}")
    out.append("")

    out.append("--- Disguised Duplicates (same responsibility, different names) ---")
    disguised = find_disguised_duplicates(report.files)
    if not disguised:
        out.append("  (none)")
    for key, locs in disguised:
        out.append(f"  [{key}]")
        for path, name, lines in locs:
            out.append(f"    - {path}  {name}  ({lines} lines)")
    out.append("")

    out.append("--- Import Hotspots (most depended-upon backend modules) ---")
    for mod, paths in find_import_hotspots(report.files)[:30]:
        out.append(f"  {mod}  <- {len(paths)} files")
        for p in paths[:5]:
            out.append(f"      * {p}")
        if len(paths) > 5:
            out.append(f"      ... +{len(paths)-5} more")
    out.append("")

    out.append("--- Oversized (>{hard}) ---")
    for f in report.oversized:
        out.append(f"  [OVER] {f.rel_path} ({f.lines})")
    if not report.oversized:
        out.append("  (none)")
    return "\n".join(out)
