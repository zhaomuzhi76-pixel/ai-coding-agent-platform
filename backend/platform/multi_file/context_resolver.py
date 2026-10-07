"""从 primary file 自动找双向相关文件。

两个方向：
    forward: primary import 谁（找它的依赖）
    reverse: 谁 import primary（找它的调用方）

纯 AST 扫描，不依赖预建索引。
"""
from __future__ import annotations

import ast
import os
from typing import Dict, List, Optional, Set, Tuple

_SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    ".idea", ".vscode", "dist", "build",
}
_DEFAULT_MAX_FILES = 6
_DEFAULT_MAX_CHARS = 8000


def _iter_py_files(workspace: str):
    for base, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                yield os.path.relpath(
                    os.path.join(base, name), workspace,
                ).replace(os.sep, "/")


def _resolve_module_to_paths(module: str) -> List[str]:
    parts = module.split(".")
    return [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
    ]


def _find_existing(workspace: str, rel: str) -> Optional[str]:
    full = os.path.join(workspace, rel)
    if os.path.isfile(full):
        return rel
    return None


def _extract_imports(source: str) -> Set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    out: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
    return out


def _module_name_of(rel_path: str) -> str:
    """'a/b/c.py' → 'a.b.c'；'a/b/__init__.py' → 'a.b'"""
    p = rel_path
    if p.endswith(".py"):
        p = p[:-3]
    if p.endswith("/__init__"):
        p = p[:-len("/__init__")]
    return p.replace("/", ".")


def _imports_target(source: str, target_module: str) -> bool:
    """source 是否 import 了 target_module（或其子模块）"""
    mods = _extract_imports(source)
    for m in mods:
        if m == target_module or m.startswith(target_module + "."):
            return True
    return False


def _read_text(full: str, max_chars: int) -> str:
    try:
        with open(full, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return ""
    if len(text) > max_chars:
        text = text[:max_chars] + "\n# ...(truncated)\n"
    return text


def resolve_related_files(
    workspace: str,
    primary_file: str,
    *,
    max_files: int = _DEFAULT_MAX_FILES,
    max_chars_per_file: int = _DEFAULT_MAX_CHARS,
    include_forward: bool = True,
    include_reverse: bool = True,
) -> Dict[str, str]:
    """返回 {rel_path: source_text}。

    forward：primary import 谁（它的依赖）
    reverse：谁 import primary（它的调用方）
    """
    if not workspace or not primary_file:
        return {}

    primary_full = os.path.join(workspace, primary_file)
    if not os.path.isfile(primary_full):
        return {}

    primary_text = _read_text(primary_full, max_chars_per_file)
    if not primary_text:
        return {}

    primary_abs = os.path.abspath(primary_full)
    primary_module = _module_name_of(primary_file)
    result: Dict[str, str] = {}

    # ── forward ─────────────────────────────────────────
    if include_forward:
        modules = _extract_imports(primary_text)
        for mod in sorted(modules):
            for cand in _resolve_module_to_paths(mod):
                rel = _find_existing(workspace, cand)
                if rel is None:
                    continue
                if os.path.abspath(
                    os.path.join(workspace, rel)
                ) == primary_abs:
                    break
                result[rel] = _read_text(
                    os.path.join(workspace, rel),
                    max_chars_per_file,
                )
                if len(result) >= max_files:
                    return result
                break

    # ── reverse ─────────────────────────────────────────
    if include_reverse:
        for rel in _iter_py_files(workspace):
            if rel == primary_file:
                continue
            if rel in result:
                continue
            full = os.path.join(workspace, rel)
            if os.path.abspath(full) == primary_abs:
                continue
            text = _read_text(full, max_chars_per_file)
            if not text:
                continue
            if _imports_target(text, primary_module):
                result[rel] = text
                if len(result) >= max_files:
                    return result

    return result


__all__ = ["resolve_related_files"]
