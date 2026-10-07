"""读取 workspace 内的源码文件。

所有路径经过 WorkspacePath.resolve 归一化（含嵌入式 WSL UNC）。
"""
from __future__ import annotations

from typing import Optional

from backend.workspace.file_ops import read_text


def ensure_source(
    source: Optional[str],
    workspace_root: str,
    path: str,
) -> str:
    """确保得到源码：已有就用，否则从磁盘读。"""
    if isinstance(source, str) and source.strip():
        return source
    return read_text(workspace_root, path)


def read_source(workspace_root: str, path: str) -> str:
    """直接读源码。"""
    return read_text(workspace_root, path)


__all__ = ["ensure_source", "read_source"]
