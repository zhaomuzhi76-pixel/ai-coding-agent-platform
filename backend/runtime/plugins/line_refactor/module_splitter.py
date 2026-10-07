"""模块拆分核心：把超限模块拆成包。

策略：
1. AST 解析，分离 imports / 顶层单元
2. 按名称引用构建依赖图
3. 弱连通分量合并，避免循环引用
4. 顺序累加，每 part ≤ soft_limit
5. 生成 __init__.py + _part_N.py
"""
from __future__ import annotations

import ast
import os
from typing import Dict, List, Set, Tuple

from backend.runtime.plugins.line_refactor.plan_models import PartSpec, SplitPlan
from backend.runtime.plugins.line_refactor.source_scanner import load_source

DEFAULT_PART_LIMIT = 180


def _is_import(node: ast.stmt) -> bool:
    return isinstance(node, (ast.Import, ast.ImportFrom))


def _top_names(node: ast.stmt) -> Set[str]:
    if isinstance(node, ast.ClassDef):
        return {node.name}
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {node.name}
    if isinstance(node, ast.Assign):
        return {t.id for t in node.targets if isinstance(t, ast.Name)}
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return {node.target.id}
    return set()


class _Unit:
    __slots__ = ("source", "names", "lines", "deps")

    def __init__(self, source: str, names: Set[str], lines: int) -> None:
        self.source = source
        self.names = names
        self.lines = lines
        self.deps: Set[int] = set()


def _build_units(tree: ast.Module) -> Tuple[List[str], List[_Unit]]:
    imports: List[str] = []
    units: List[_Unit] = []
    for idx, node in enumerate(tree.body):
        if _is_import(node):
            imports.append(ast.unparse(node))
            continue
        if idx == 0 and isinstance(node, ast.Expr) \
                and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            continue  # 模块 docstring
        try:
            src = ast.unparse(node)
        except Exception:
            src = ""
        names = _top_names(node)
        units.append(_Unit(source=src, names=names, lines=src.count("\n") + 1))
    return imports, units


def _link_deps(units: List[_Unit]) -> None:
    name_to_unit: Dict[str, _Unit] = {}
    for u in units:
        for n in u.names:
            name_to_unit[n] = u
    for u in units:
        try:
            parsed = ast.parse(u.source)
        except SyntaxError:
            continue
        for child in ast.walk(parsed):
            if isinstance(child, ast.Name):
                target = name_to_unit.get(child.id)
                if target is not None and target is not u:
                    u.deps.add(id(target))


def _weak_components(units: List[_Unit]) -> List[List[_Unit]]:
    id_to_unit = {id(u): u for u in units}
    adj: Dict[int, Set[int]] = {id(u): set() for u in units}
    for u in units:
        for d in u.deps:
            adj[id(u)].add(d)
            adj[d].add(id(u))
    seen: Set[int] = set()
    comps: List[List[_Unit]] = []
    for u in units:
        if id(u) in seen:
            continue
        stack = [id(u)]
        comp: List[_Unit] = []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(id_to_unit[cur])
            for nxt in adj[cur]:
                if nxt not in seen:
                    stack.append(nxt)
        order = {id(x): i for i, x in enumerate(units)}
        comp.sort(key=lambda x: order[id(x)])
        comps.append(comp)
    return comps


def _pack_parts(comps: List[List[_Unit]], soft: int) -> List[List[_Unit]]:
    parts: List[List[_Unit]] = []
    current: List[_Unit] = []
    current_lines = 0
    for comp in comps:
        comp_lines = sum(u.lines for u in comp)
        if current and current_lines + comp_lines > soft:
            parts.append(current)
            current = []
            current_lines = 0
        current.extend(comp)
        current_lines += comp_lines
    if current:
        parts.append(current)
    return parts


def _render_part(idx: int, units: List[_Unit], imports: List[str],
                 all_names: Set[str]) -> PartSpec:
    lines: List[str] = [f'"""Auto-split part {idx}."""', ""]
    lines.extend(imports)
    lines.append("")
    exported: List[str] = []
    for u in units:
        lines.append(u.source)
        lines.append("")
        for n in sorted(u.names):
            if n in all_names:
                exported.append(n)
    lines.append(f"__all__ = {sorted(set(exported))!r}")
    return PartSpec(
        filename=f"_part_{idx}.py",
        source="\n".join(lines),
        exported_names=sorted(set(exported)),
    )


def _skip(path: str, original_lines: int, reason: str) -> SplitPlan:
    return SplitPlan(
        source_path=path, package_dir="", original_lines=original_lines,
        init_source="", skipped_reason=reason,
    )


def build_split_plan(path: str, soft: int = DEFAULT_PART_LIMIT) -> SplitPlan:
    source = load_source(path)
    original_lines = source.count("\n") + 1
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return _skip(path, original_lines, f"syntax_error:{exc}")
    imports, units = _build_units(tree)
    if not units:
        return _skip(path, original_lines, "no_top_level_units")
    _link_deps(units)
    comps = _weak_components(units)
    parts = _pack_parts(comps, soft)
    if len(parts) < 2:
        return _skip(path, original_lines, "cannot_reduce_below_soft_limit")
    all_names: Set[str] = set()
    for u in units:
        all_names |= u.names
    part_specs = [
        _render_part(i, part, imports, all_names)
        for i, part in enumerate(parts)
    ]
    pkg_dir = path[:-3]
    init_lines: List[str] = [
        f'"""Package split from {os.path.basename(path)}."""',
        "",
    ]
    init_lines.extend(imports)
    init_lines.append("")
    for spec in part_specs:
        mod = spec.filename[:-3]
        for n in spec.exported_names:
            init_lines.append(f"from .{mod} import {n}")
    init_lines.append("")
    init_lines.append(f"__all__ = {sorted(all_names)!r}")
    return SplitPlan(
        source_path=path,
        package_dir=pkg_dir,
        original_lines=original_lines,
        init_source="\n".join(init_lines),
        parts=part_specs,
    )
