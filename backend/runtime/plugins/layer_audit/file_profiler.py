"""单文件结构剖析。"""
from __future__ import annotations

import ast
import os
from typing import List

from backend.runtime.plugins.layer_audit.audit_models import FileProfile, Unit


def _lines(node: ast.stmt) -> int:
    return len(ast.unparse(node).splitlines())


def _class_methods(node: ast.ClassDef):
    names: List[str] = []
    lns: List[int] = []
    for m in node.body:
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(m.name)
            lns.append(_lines(m))
    return names, lns


def _kind_of(node: ast.stmt) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.FunctionDef):
        return "function"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async_function"
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        return "assign"
    return "other"


def _unit_of(node: ast.stmt) -> Unit:
    k = _kind_of(node)
    if k == "class":
        assert isinstance(node, ast.ClassDef)
        names, lns = _class_methods(node)
        return Unit(kind=k, name=node.name, lines=_lines(node),
                    methods=names, method_lines=lns)
    if k in ("function", "async_function"):
        return Unit(kind=k, name=node.name, lines=_lines(node))
    if k == "assign":
        name = "<assign>"
        if isinstance(node, ast.Assign) and node.targets \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign) \
                and isinstance(node.target, ast.Name):
            name = node.target.id
        return Unit(kind=k, name=name, lines=_lines(node))
    return Unit(kind="other", name=type(node).__name__, lines=_lines(node))


def _collect_imports(tree: ast.Module):
    all_imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                all_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            all_imports.append(node.module)
    return all_imports


def profile(path: str, root: str) -> FileProfile:
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    total = source.count("\n") + 1
    tree = ast.parse(source)
    imports = _collect_imports(tree)
    units: List[Unit] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            continue
        units.append(_unit_of(node))
    return FileProfile(path=path, rel_path=rel, lines=total,
                       imports=imports, units=units)
