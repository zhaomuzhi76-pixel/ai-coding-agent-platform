"""L2 共享文件遍历：统一 walk 语义。

职责：
  - 单一遍历语义（跳过 .git / node_modules / __pycache__ 等）
  - 返回统一的 (rel_path, abs_path) 元组

不负责：
  - 文件内容读/写
  - 搜索/过滤逻辑（调用方决定）
  - 索引（那是 workspace 领域的事）

被 L2 服务复用：
  - agent_entry.query_handler
  - agent_loop.tool_registry
"""
from __future__ import annotations

import os
from typing import Iterator

from backend.workspace.path_normalizer import normalize_workspace_path

SKIP_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".idea", ".vscode", "dist", "build", ".next", "target",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
})


def walk_files(workspace: str) -> Iterator[tuple[str, str]]:
    """遍历工作区文件。

    产出：(POSIX 风格相对路径, 绝对路径)
    自动跳过 SKIP_DIRS 中的目录。
    """
    root = normalize_workspace_path(workspace)
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            full = os.path.join(base, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            yield rel, full


__all__ = ["walk_files", "SKIP_DIRS"]
