"""工作区文件操作边界。所有 read/write/stat 必须经过此模块。

强制经过 WorkspacePath.resolve()，保证：
  - 路径归一化（含嵌入式 WSL UNC）
  - 拒绝逃逸出工作区的路径
"""
from __future__ import annotations

import os

from .workspace_path import resolve


def read_text(workspace_root: str, path: str) -> str:
    wp = resolve(workspace_root, path)
    with open(str(wp), "r", encoding="utf-8") as fh:
        return fh.read()


def read_bytes(workspace_root: str, path: str) -> bytes:
    wp = resolve(workspace_root, path)
    with open(str(wp), "rb") as fh:
        return fh.read()


def write_text(workspace_root: str, path: str, content: str) -> None:
    wp = resolve(workspace_root, path)
    parent = os.path.dirname(str(wp))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(str(wp), "w", encoding="utf-8") as fh:
        fh.write(content)


def exists(workspace_root: str, path: str) -> bool:
    try:
        wp = resolve(workspace_root, path)
    except Exception:
        return False
    return os.path.isfile(str(wp))


__all__ = ["read_text", "read_bytes", "write_text", "exists"]
