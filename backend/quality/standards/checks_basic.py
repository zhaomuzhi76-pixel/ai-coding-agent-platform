"""standards 独有 check：库禁 exit（project_rules 未覆盖）。

已删除的重复项（迁移到 backend.project_rules.checks）：
  - check_line_limit       → checks/file_size_check.FileSizeChecker
  - check_layer_order      → checks/layer_purity_check.LayerPurityChecker

不重复职责：只保留 project_rules 没有的能力。
"""
from __future__ import annotations

import ast
from pathlib import Path

from backend.quality.standards.contracts import CheckResult


def _is_dunder_main_block(node: ast.AST) -> bool:
    """判断节点是否在 `if __name__ == "__main__":` 块内。"""
    if not isinstance(node, ast.If):
        return False
    try:
        cmp = node.test
        if not isinstance(cmp, ast.Compare):
            return False
        if not isinstance(cmp.left, ast.Name):
            return False
        if cmp.left.id != "__name__":
            return False
        if not cmp.comparators:
            return False
        right = cmp.comparators[0]
        return isinstance(right, ast.Constant) and right.value == "__main__"
    except Exception:
        return False


def _collect_main_block_lines(tree: ast.Module) -> set[int]:
    out: set[int] = set()
    for node in tree.body:
        if _is_dunder_main_block(node):
            for sub in ast.walk(node):
                if hasattr(sub, "lineno"):
                    out.add(sub.lineno)
    return out


def check_no_exit(path: Path, rel: str) -> CheckResult:
    """库函数内禁止 exit / SystemExit；
    `if __name__ == "__main__":` 块内允许（Python 传退出码唯一方式）。
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return CheckResult("no_exit", True, rel, "skip (syntax)")

    allowed = _collect_main_block_lines(tree)
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                if fn.attr in ("exit", "_exit") and node.lineno not in allowed:
                    bad.append(f"line {node.lineno}: .{fn.attr}()")
            elif isinstance(fn, ast.Name) and fn.id == "exit" \
                    and node.lineno not in allowed:
                bad.append(f"line {node.lineno}: exit()")
        elif isinstance(node, ast.Raise) and node.exc:
            if isinstance(node.exc, ast.Call) and node.lineno not in allowed:
                nm = getattr(node.exc.func, "id", "")
                if nm == "SystemExit":
                    bad.append(f"line {node.lineno}: SystemExit")
    if bad:
        return CheckResult("no_exit", False, rel,
                           "库函数内禁止 exit: " + "; ".join(bad[:3]))
    return CheckResult("no_exit", True, rel, "")


__all__ = ["check_no_exit"]
