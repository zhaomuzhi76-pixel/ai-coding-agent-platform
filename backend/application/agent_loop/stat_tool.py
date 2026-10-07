"""file_stat：只读文件元数据（大小/时间/类型）。

工业级契约：
  - 只读，永不修改 workspace
  - 路径经 WorkspaceFileAccess.resolve（拒穿越）
  - 返回 size / mtime / is_dir / is_file / is_symlink / mode
  - 不读内容（与 read_file 职责分离）
"""
from __future__ import annotations

import os
import stat as _stat
import time
from typing import Optional

from .tool_spec import ToolSpec
from ._shared import get_access


def _safe_rel(workspace: str, path: str) -> Optional[str]:
    """返回真实路径；越权返回 None。"""
    try:
        acc = get_access(workspace)
        target = acc.resolve(path)
        return str(target)
    except Exception:
        return None


def _file_stat(workspace: str, path: str) -> dict:
    if not path or not str(path).strip():
        return {"ok": False, "error": "path required"}
    real = _safe_rel(workspace, str(path).strip())
    if real is None:
        return {"ok": False, "error": f"path traversal: {path}", "path": path}
    try:
        st = os.lstat(real)
    except FileNotFoundError:
        return {"ok": False, "error": f"not found: {path}", "path": path}
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "path": path}
    return {
        "ok": True,
        "path": path,
        "size": st.st_size,
        "mtime": st.st_mtime,
        "mtime_human": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
        "is_dir": _stat.S_ISDIR(st.st_mode),
        "is_file": _stat.S_ISREG(st.st_mode),
        "is_symlink": _stat.S_ISLNK(st.st_mode),
        "mode": oct(st.st_mode & 0o777),
    }


FILE_STAT_TOOL = ToolSpec(
    "file_stat",
    "读取文件元数据（大小/时间/类型），不读内容。",
    {"path": "工作区相对路径"},
)


def dispatch_file_stat(args: dict, workspace: str) -> dict:
    return _file_stat(workspace, str(args.get("path", "")))


__all__ = ["FILE_STAT_TOOL", "dispatch_file_stat", "_file_stat"]
