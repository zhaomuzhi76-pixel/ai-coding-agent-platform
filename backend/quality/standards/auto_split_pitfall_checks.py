"""自动拆分避坑 —— 项目自检实现（从 auto_split_pitfalls 抽出）。"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List

def check_all() -> List[dict]:
    """一条命令跑自检：扫项目里是否还有未修复的坑。"""
    import ast
    from pathlib import Path

    root = Path("backend")
    results: List[dict] = []

    # 1) @staticmethod 缺失
    static_names = set()
    for bak in root.rglob("*.py.bak_autosplit"):
        try:
            tree = ast.parse(bak.read_text(encoding="utf-8"))
        except Exception:
            continue
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for m in cls.body:
                if not isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if any(
                    isinstance(d, ast.Name) and d.id == "staticmethod"
                    for d in m.decorator_list
                ):
                    static_names.add(m.name)

    missing_static = []
    for d in root.rglob("_*_parts"):
        for f in d.rglob("*.py"):
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
                for m in cls.body:
                    if not isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    if m.name in static_names and not any(
                        isinstance(d2, ast.Name) and d2.id == "staticmethod"
                        for d2 in m.decorator_list
                    ):
                        missing_static.append(f"{f}:{m.lineno} {m.name}")

    if missing_static:
        results.append({
            "pitfall": "decorator_loss_staticmethod",
            "count": len(missing_static),
            "files": missing_static[:10],
        })

    # 2) _stmt_ 泄漏
    stmt_leaks = []
    for d in root.rglob("_*_parts"):
        for f in d.rglob("*.py"):
            try:
                txt = f.read_text(encoding="utf-8")
            except Exception:
                continue
            if "_stmt_" in txt:
                stmt_leaks.append(str(f))
    if stmt_leaks:
        results.append({
            "pitfall": "stmt_placeholder_leaked",
            "count": len(stmt_leaks),
            "files": stmt_leaks[:10],
        })

    # 3) except: pass 静默吞
    silent = []
    for f in root.rglob("*.py"):
        if "_*_parts" in str(f):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, ln in enumerate(txt.split("\n"), 1):
            if ln.strip() == "pass" and i > 1:
                prev = txt.split("\n")[i - 2].strip()
                # 只报宽泛 `except Exception:`（类型化 except 是精准捕获，非坑）
                if prev == "except Exception:":
                    silent.append(f"{f}:{i}")
    if silent:
        results.append({
            "pitfall": "silent_exception_swallow",
            "count": len(silent),
            "files": silent[:10],
        })

    return results


__all__ = ["check_all"]
