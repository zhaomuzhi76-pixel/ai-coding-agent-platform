"""WorkspaceFileAccess 缓存（消重）。

tool_registry / write_tools 原先各定义 _get_access（重复）。
统一到此处，两者共享同一进程内缓存。
"""
from __future__ import annotations

import os

from backend.workspace.file_access import WorkspaceFileAccess

_ACCESS_CACHE: dict[str, WorkspaceFileAccess] = {}


def get_access(workspace: str) -> WorkspaceFileAccess:
    key = os.path.abspath(workspace)
    acc = _ACCESS_CACHE.get(key)
    if acc is None:
        acc = WorkspaceFileAccess(key)
        _ACCESS_CACHE[key] = acc
    return acc


__all__ = ["get_access"]
