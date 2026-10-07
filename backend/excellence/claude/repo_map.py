"""RepoMap: whole-repository structural map (Claude Code: 全仓库理解).

聚合目录树 + 模块摘要 + 大小分布 + 语言统计，
不重复 ProjectAnalysisFacade（后者做语义分析），本类只做结构聚合。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

_SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}


@dataclass
class ModuleNode:
    path: str
    lines: int
    package: str = ""
    top_classes: int = 0
    top_funcs: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "lines": self.lines,
            "package": self.package,
            "top_classes": self.top_classes,
            "top_funcs": self.top_funcs,
        }


@dataclass
class RepoMap:
    root: str
    files: List[ModuleNode] = field(default_factory=list)
    packages: Dict[str, int] = field(default_factory=dict)

    @property
    def total_lines(self) -> int:
        return sum(f.lines for f in self.files)

    @property
    def total_files(self) -> int:
        return len(self.files)

    def largest(self, n: int = 10) -> List[ModuleNode]:
        return sorted(self.files, key=lambda x: -x.lines)[:n]

    def by_package(self) -> List[tuple]:
        return sorted(self.packages.items(), key=lambda x: -x[1])

    def dump(self) -> Dict[str, Any]:
        return {
            "root": self.root,
            "files": self.total_files,
            "total_lines": self.total_lines,
            "packages": len(self.packages),
        }


class RepoMapper:
    VERSION = "1.0"

    def __init__(self, skip_dirs: tuple = tuple(_SKIP_DIRS)) -> None:
        self._skip = set(skip_dirs)

    def build(self, root: str) -> RepoMap:
        import ast
        m = RepoMap(root=root)
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in self._skip]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(base, name)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                try:
                    with open(path, "r", encoding="utf-8",
                              errors="ignore") as fh:
                        src = fh.read()
                except OSError:
                    continue
                lines = src.count("\n") + 1
                package = os.path.dirname(rel) or "."
                top_classes = top_funcs = 0
                try:
                    tree = ast.parse(src)
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef):
                            top_classes += 1
                        elif isinstance(node, (ast.FunctionDef,
                                                ast.AsyncFunctionDef)):
                            top_funcs += 1
                except SyntaxError:
                    pass
                m.files.append(ModuleNode(
                    path=rel, lines=lines, package=package,
                    top_classes=top_classes, top_funcs=top_funcs,
                ))
                m.packages[package] = m.packages.get(package, 0) + 1
        return m

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["ModuleNode", "RepoMap", "RepoMapper"]
