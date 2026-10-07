"""[薄适配层] 兼容旧接口 —— 委托到唯一权威实现。

历史：本模块曾独立实现 normalize_workspace_path，
      与 workspace_path._canonicalize 重复。
现在：唯一权威实现是 workspace_path.normalize_only。
      本模块只保留公共 API 兼容（29 处 import 不变）。

新代码请直接：
    from backend.workspace.workspace_path import normalize_only
"""
from __future__ import annotations

from pathlib import Path

from backend.workspace.workspace_path import normalize_only


def normalize_workspace_path(path: str) -> str:
    """[兼容] 归一化路径。委托给权威实现。

    行为与历史一致：非法输入原样返回，不抛异常。
    """
    return normalize_only(path)


def canonical_workspace_path(path: str) -> str:
    """[兼容] 先归一化，再 resolve（若存在）。"""
    normalized = normalize_only(path)
    if not normalized:
        return normalized
    try:
        return str(Path(normalized).resolve())
    except (OSError, RuntimeError):
        return normalized


__all__ = ["normalize_workspace_path", "canonical_workspace_path"]
