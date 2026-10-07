"""Resolve LLM-provided file path to a real workspace path.

与 workspace.WorkspaceIndex.find_file 的区别：
    WorkspaceIndex.find_file(keyword)
        → 模糊 substring 搜索（keyword in path）
        → 需要预构建索引
        → 返回 list[dict]，供搜索工具用

    path_resolver.resolve_path(workspace_root, path)
        → 精确 basename 匹配（name == basename）
        → 无状态实时扫描
        → 唯一命中返回真路径，多命中报错
        → 供 executor 在「LLM 只给了文件名」时修正

场景：
    LLM 返回 'FUNDING.yml'，真实文件在 '.github/FUNDING.yml'。
    本模块唯一化路径，不重复 WorkspaceIndex 的搜索职责。
"""
from __future__ import annotations

import os
from typing import List, Optional

_MAX_SCAN_FILES = 20000
_SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    ".idea", ".vscode", "dist", "build",
}


def _exists(workspace_root: str, path: str) -> bool:
    candidate = (
        path if os.path.isabs(path)
        else os.path.join(workspace_root, path)
    )
    return os.path.isfile(candidate)


def _is_bare_filename(path: str) -> bool:
    """没有目录分隔符（既非绝对也非相对目录）。"""
    p = path.strip()
    return "/" not in p and "\\" not in p and not p.startswith(".")


def _scan_by_basename(
    workspace_root: str, basename: str,
) -> List[str]:
    hits: List[str] = []
    count = 0
    for base, dirs, files in os.walk(workspace_root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            count += 1
            if count > _MAX_SCAN_FILES:
                return hits
            if name == basename:
                rel = os.path.relpath(
                    os.path.join(base, name), workspace_root,
                ).replace(os.sep, "/")
                hits.append(rel)
    return hits


def resolve_path(
    workspace_root: str,
    path: Optional[str],
) -> Optional[str]:
    """Return a workspace-relative (or absolute) path that exists.

    规则：
        1. 空路径或绝对路径 → 原样返回
        2. 相对路径存在 → 原样返回
        3. 仅文件名（无目录）→ 全工作区搜索 basename
            - 唯一命中 → 返回真实相对路径
            - 多个命中 → 报错，让 LLM/用户明确
            - 无命中 → 原样返回（后续 loader 会报清晰错误）
    """
    if not isinstance(path, str) or not path.strip():
        return path
    p = path.strip()

    if os.path.isabs(p):
        return p

    if _exists(workspace_root, p):
        return p

    if not _is_bare_filename(p):
        return p

    basename = os.path.basename(p)
    hits = _scan_by_basename(workspace_root, basename)

    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        joined = ", ".join(sorted(hits)[:10])
        raise RuntimeError(
            f"ambiguous filename '{basename}' in workspace "
            f"({len(hits)} matches): {joined}. "
            f"请指定更完整的路径。"
        )
    return p


__all__ = ["resolve_path"]
