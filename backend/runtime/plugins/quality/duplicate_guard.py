"""重复职责守卫：防止未来新增文件引入重复实现。"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from typing import Dict, List

PROTECTED_NAMES = frozenset({
    # runtime/executors/_shared
    "required_context_value",
    "apply_kind",
    "validate_node",
    # memory/_shared/schema
    "init_rules_patches",
    "init_code_index",
    "init_skills",
    "init_error_fixes",
    # providers/_shared
    "LLMProviderBase",
    "required_model",
})

_SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}


@dataclass
class DuplicateFinding:
    name: str
    locations: List[str] = field(default_factory=list)


def _iter_py(root: str):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def _top_level_defs(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (SyntaxError, OSError):
        return []
    found: List[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in PROTECTED_NAMES:
                found.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if node.name in PROTECTED_NAMES:
                found.append(node.name)
    return found


def scan(root: str) -> List[DuplicateFinding]:
    name_to_locs: Dict[str, List[str]] = {}
    for path in _iter_py(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        for name in _top_level_defs(path):
            name_to_locs.setdefault(name, []).append(rel)
    return [
        DuplicateFinding(name=n, locations=sorted(set(ls)))
        for n, ls in name_to_locs.items() if len(set(ls)) > 1
    ]


__all__ = ["PROTECTED_NAMES", "DuplicateFinding", "scan"]
