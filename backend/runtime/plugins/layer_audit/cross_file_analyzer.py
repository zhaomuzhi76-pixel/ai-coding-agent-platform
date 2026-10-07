"""跨文件分析：重复职责、层内依赖。"""
from __future__ import annotations

from typing import Dict, List, Set

from backend.runtime.plugins.layer_audit.audit_models import (
    AuditReport,
    DuplicateHit,
    FileProfile,
)


def _module_of(rel_path: str) -> str:
    return rel_path[:-3].replace("/", ".") if rel_path.endswith(".py") else rel_path


def find_duplicates(files: List[FileProfile], kind: str) -> List[DuplicateHit]:
    name_to_files: Dict[str, List[str]] = {}
    for f in files:
        for u in f.units:
            if u.kind != kind:
                continue
            name_to_files.setdefault(u.name, []).append(f.rel_path)
    hits = [
        DuplicateHit(name=n, kind=kind, files=sorted(set(fs)))
        for n, fs in name_to_files.items() if len(set(fs)) > 1
    ]
    hits.sort(key=lambda h: (-len(h.files), h.name))
    return hits


def find_internal_edges(files: List[FileProfile]) -> List[tuple]:
    rel_set: Set[str] = {f.rel_path for f in files}
    module_to_rel: Dict[str, str] = {
        _module_of(f.rel_path): f.rel_path for f in files
    }
    edges: List[tuple] = []
    seen: Set[tuple] = set()
    for f in files:
        for imp in f.imports:
            for mod, rel in module_to_rel.items():
                if rel == f.rel_path:
                    continue
                if imp == mod or imp.startswith(mod + "."):
                    edge = (f.rel_path, rel)
                    if edge not in seen:
                        seen.add(edge)
                        edges.append(edge)
                    break
    edges.sort()
    return edges


def build_report(root: str, files: List[FileProfile],
                 hard: int = 230) -> AuditReport:
    report = AuditReport(root=root, files=files)
    report.duplicate_classes = find_duplicates(files, "class")
    report.duplicate_functions = find_duplicates(files, "function")
    report.duplicate_functions.extend(find_duplicates(files, "async_function"))
    report.internal_import_edges = find_internal_edges(files)
    report.oversized = [f for f in files if f.lines > hard]
    return report
