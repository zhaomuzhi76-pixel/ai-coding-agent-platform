"""超限文件诊断：输出结构化拆包建议。"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import List


@dataclass
class UnitInfo:
    kind: str
    name: str
    lines: int
    methods: List[str] = field(default_factory=list)
    method_lines: List[int] = field(default_factory=list)


@dataclass
class FileDiagnosis:
    path: str
    total_lines: int
    imports_lines: int
    units: List[UnitInfo] = field(default_factory=list)
    recommendation: str = ""

    def summary(self) -> str:
        lines = [f"### {self.path}  ({self.total_lines} lines)"]
        lines.append(f"  imports: {self.imports_lines} lines")
        for u in self.units:
            lines.append(f"  [{u.kind}] {u.name}: {u.lines} lines")
            for m, ml in zip(u.methods, u.method_lines):
                lines.append(f"      - {m}: {ml} lines")
        lines.append(f"  -> {self.recommendation}")
        return "\n".join(lines)


def _lines(node: ast.stmt) -> int:
    return len(ast.unparse(node).splitlines())


def _kind(node: ast.stmt) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function"
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "import"
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        return "assign"
    return "other"


def _methods(node: ast.ClassDef):
    names: List[str] = []
    lns: List[int] = []
    for m in node.body:
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(m.name)
            lns.append(_lines(m))
    return names, lns


def _recommend(total: int, units: List[UnitInfo]) -> str:
    if total <= 180:
        return "already small"
    classes = [u for u in units if u.kind == "class"]
    funcs = [u for u in units if u.kind == "function"]
    if len(classes) >= 2:
        return f"split into package: one file per class ({len(classes)} classes)"
    if len(classes) == 1:
        c = classes[0]
        if c.lines > 180 and len(c.methods) >= 4:
            return (f"single big class '{c.name}' with {len(c.methods)} methods; "
                    f"manual mixin split required")
        return f"single class '{c.name}'; manual extraction recommended"
    if len(funcs) >= 3:
        return f"split {len(funcs)} functions into helpers + main module"
    return "manual review required"


def diagnose(path: str) -> FileDiagnosis:
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    total = source.count("\n") + 1
    tree = ast.parse(source)
    imports_lines = 0
    units: List[UnitInfo] = []
    for node in tree.body:
        k = _kind(node)
        if k == "import":
            imports_lines += _lines(node)
            continue
        if k == "class":
            assert isinstance(node, ast.ClassDef)
            names, lns = _methods(node)
            units.append(UnitInfo(kind="class", name=node.name,
                                  lines=_lines(node),
                                  methods=names, method_lines=lns))
        elif k == "function":
            assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            units.append(UnitInfo(kind="function", name=node.name, lines=_lines(node)))
        elif k == "assign":
            name = "<assign>"
            if isinstance(node, ast.Assign) and node.targets \
                    and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
            units.append(UnitInfo(kind="assign", name=name, lines=_lines(node)))
        else:
            units.append(UnitInfo(kind="other", name=type(node).__name__,
                                  lines=_lines(node)))
    return FileDiagnosis(
        path=path, total_lines=total, imports_lines=imports_lines,
        units=units, recommendation=_recommend(total, units),
    )
