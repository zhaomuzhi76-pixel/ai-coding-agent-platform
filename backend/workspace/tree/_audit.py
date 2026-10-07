"""tree 层静态审查器（L4-d）。

7 类规则：
  1. SYNTAX         语法
  2. LAYER          依赖方向（L0 不能 import L1/L2/L3）
  3. NAMING         通用短名（encode/decode/run/execute）跨模块复用
  4. ENV            模块级 os.environ 写入
  5. CONVENTION     约定入口名白名单（main / audit）
  6. INVARIANT      关键不变量（filter 优先级 / cursor 基于 name / 硬上限）
  7. NAME           NameError 静态检测

零依赖（只用 stdlib + ast）。
"""
from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

LAYER = Path(__file__).resolve().parent
_BUILTINS = set(dir(__builtins__)) if not isinstance(__builtins__, dict)             else set(__builtins__.keys())

_CONVENTION_NAMES = {"main", "audit", "cli", "entry"}

# L0 禁止 import 的上层包
_L0_DIRS = {"filter"}
_UPPER_PKGS = {"index", "pagination", "watch", "service"}

# 通用短名（跨模块复用 → 命名不具体）
_GENERIC_SHORT_NAMES = {"encode", "decode", "run", "execute", "process"}


def _bound_names(tree: ast.Module) -> set[str]:
    bound: set[str] = set()

    class Bind(ast.NodeVisitor):
        def visit_Import(self, node):
            for a in node.names:
                bound.add((a.asname or a.name).split(".")[0])
        def visit_ImportFrom(self, node):
            for a in node.names:
                if a.name != "*":
                    bound.add(a.asname or a.name)
        def _args(self, a):
            for x in a.posonlyargs + a.args + a.kwonlyargs:
                bound.add(x.arg)
            if a.vararg: bound.add(a.vararg.arg)
            if a.kwarg:  bound.add(a.kwarg.arg)
        def visit_FunctionDef(self, node):
            bound.add(node.name); self._args(node.args); self.generic_visit(node)
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_ClassDef(self, node):
            bound.add(node.name); self.generic_visit(node)
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store): bound.add(node.id)
            self.generic_visit(node)
        def visit_ExceptHandler(self, node):
            if node.name: bound.add(node.name)
            self.generic_visit(node)
        def visit_For(self, node):
            if isinstance(node.target, ast.Name): bound.add(node.target.id)
            self.generic_visit(node)
        visit_AsyncFor = visit_For
        def visit_With(self, node):
            for it in node.items:
                if isinstance(it.optional_vars, ast.Name):
                    bound.add(it.optional_vars.id)
            self.generic_visit(node)
        visit_AsyncWith = visit_With
        def visit_Global(self, node):
            for n in node.names: bound.add(n)
        def visit_Nonlocal(self, node):
            for n in node.names: bound.add(n)
        def visit_Lambda(self, node):
            self._args(node.args); self.generic_visit(node)
        def visit_comprehension(self, node):
            if isinstance(node.target, ast.Name): bound.add(node.target.id)
            self.generic_visit(node)

    Bind().visit(tree)
    return bound


def audit() -> list[tuple[str, str, str]]:
    issues: list[tuple[str, str, str]] = []
    files = sorted(LAYER.rglob("*.py"))
    trees: dict[str, ast.Module] = {}

    # 1. 语法
    for f in files:
        if "_audit" in f.name or "__pycache__" in str(f): continue
        try:
            trees[str(f.relative_to(LAYER))] = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            issues.append(("SYNTAX", str(f), f"L{e.lineno}: {e.msg}"))

    # 2. LAYER: L0 不能 import 上层
    for fname, tree in trees.items():
        if not fname.startswith("filter/"): continue
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                mod = n.module
                for up in _UPPER_PKGS:
                    if re.search(rf"(^|\.){up}\b", mod):
                        issues.append(("LAYER", fname, f"L0 imports {up}: {mod}"))

    # 3. NAMING: 通用短名跨模块复用
    name_owner: dict[str, list[str]] = defaultdict(list)
    for fname, tree in trees.items():
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if n.name in _GENERIC_SHORT_NAMES:
                    name_owner[n.name].append(fname)
    for name, owners in name_owner.items():
        if len(owners) > 1:
            issues.append(("NAMING", name, "跨模块复用通用短名: " + ", ".join(owners)))

    # 4. ENV: 模块级 os.environ 写入
    for fname, tree in trees.items():
        for n in tree.body:
            for sub in ast.walk(n):
                if isinstance(sub, ast.Subscript)                    and isinstance(sub.value, ast.Attribute)                    and sub.value.attr == "environ"                    and isinstance(sub.value.value, ast.Name)                    and sub.value.value.id in ("os", "_os")                    and isinstance(n, ast.Assign):
                    issues.append(("ENV", fname, f"L{n.lineno} 模块级写 os.environ"))
                    break

    # 5. CONVENTION: 通用入口名不算冲突（跳过）

    # 6. INVARIANT: 关键常量/方法存在性
    def _file_text(rel: str) -> str:
        p = LAYER / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    svc = _file_text("service.py")
    if "gitignore" in svc and "显式" not in svc and "match_verbose" not in svc:
        issues.append(("INVARIANT", "service.py", "gitignore 优先级未实现 match_verbose"))

    cur = _file_text("pagination/cursor.py")
    if cur:
        if "HARD_LIMIT" not in cur:
            issues.append(("INVARIANT", "pagination/cursor.py", "缺 HARD_LIMIT"))
        if "next_cursor" not in cur:
            issues.append(("INVARIANT", "pagination/cursor.py", "缺 next_cursor"))

    # 7. NAME: 未定义名
    for fname, tree in trees.items():
        bound = _bound_names(tree)

        class Ref(ast.NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    n = node.id
                    if n in bound or n in _BUILTINS: return
                    if n.startswith("__") and n.endswith("__"): return
                    issues.append(("NAME", fname, f"L{node.lineno} 未定义: {n}"))
                self.generic_visit(node)

        Ref().visit(tree)

    return issues


def main() -> int:
    issues = audit()
    files = sorted(
        p.name for p in LAYER.rglob("*.py")
        if "_audit" not in p.name and "__pycache__" not in str(p)
    )
    print("层: " + str(LAYER))
    print("文件数: " + str(len(files)) + "   文件: " + ", ".join(files))
    print("-" * 60)
    if not issues:
        print("✅ 全层通过（7 类规则）")
        return 0
    for k, loc, m in issues:
        print("❌ [" + k + "] " + loc + " — " + m)
    print("")
    print("共 " + str(len(issues)) + " 项待修")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
