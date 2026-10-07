"""写工具集：write_file / edit_file / delete_file。

工业级契约：
  - 路径经 WorkspaceFileAccess.resolve（拒绝目录穿越）
  - 写入前自动备份到 .agent_backup/<ts>/
  - 单次写入 ≤ 1MB
"""
from __future__ import annotations

import asyncio

import os
import shutil
import time
from pathlib import Path

from backend.workspace.file_access import WorkspaceFileAccess

from .tool_spec import ToolSpec
from ._shared import get_access

_MAX_WRITE_BYTES = 1_000_000
_BACKUP_DIR = ".agent_backup"

def _normalize_rel(workspace: str, rel_path: str) -> Path | None:
    """归一化 rel_path 为 workspace 内相对路径。

    处理 pathlib 陷阱：Path(base) / "/abs/path" == "/abs/path"
    → 造成 SameFileError。
    """
    p = Path(rel_path)
    if not p.is_absolute():
        return p
    try:
        return p.relative_to(Path(workspace).resolve())
    except ValueError:
        # workspace 外 → 用 basename 兜底（不泄露绝对路径）
        return Path(p.name)


def _backup(workspace: str, rel_path: str) -> str | None:
    acc = get_access(workspace)
    try:
        target = acc.resolve(rel_path)
    except PermissionError:
        return None
    if not target.is_file():
        return None
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup_root = Path(workspace) / _BACKUP_DIR / ts
    rel = _normalize_rel(workspace, rel_path)
    if rel is None:
        return None
    backup_path = backup_root / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_path)
    return str(backup_path.relative_to(Path(workspace)))


def _write_file(workspace: str, path: str, content: str) -> dict:
    if not path.strip():
        return {"ok": False, "error": "path required"}
    if len(content) > _MAX_WRITE_BYTES:
        return {"ok": False, "error": f"content too large ({len(content)})"}
    backup = _backup(workspace, path)
    try:
        acc = get_access(workspace)
        acc.write_text(path, content)
    except PermissionError as exc:
        return {"ok": False, "error": f"path traversal: {exc}"}
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "path": path, "size": len(content), "backup": backup}


def _edit_file(workspace: str, path: str, old: str, new: str) -> dict:
    if not path.strip():
        return {"ok": False, "error": "path required"}
    if not old:
        return {"ok": False, "error": "old text required"}
    try:
        acc = get_access(workspace)
        original = acc.read_text(path)
    except PermissionError as exc:
        return {"ok": False, "error": f"path traversal: {exc}"}
    except FileNotFoundError:
        return {"ok": False, "error": f"file not found: {path}"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if old not in original:
        return {"ok": False, "error": "old text not found in file"}
    updated = original.replace(old, new, 1)
    backup = _backup(workspace, path)
    try:
        acc.write_text(path, updated)
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "path": path,
            "delta": len(updated) - len(original), "backup": backup}


def _delete_file(workspace: str, path: str) -> dict:
    if not path.strip():
        return {"ok": False, "error": "path required"}
    try:
        acc = get_access(workspace)
        target = acc.resolve(path)
    except PermissionError as exc:
        return {"ok": False, "error": f"path traversal: {exc}"}
    if not target.is_file():
        return {"ok": False, "error": f"not a file: {path}"}
    backup = _backup(workspace, path)
    try:
        target.unlink()
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "path": path, "backup": backup}


WRITE_TOOLS: dict[str, ToolSpec] = {
    "write_file": ToolSpec(
        "write_file",
        "写入文件（覆盖，自动备份）。",
        {"path": "工作区相对路径", "content": "文件内容"},
    ),
    "edit_file": ToolSpec(
        "edit_file",
        "替换文件中一段文本（首次匹配，自动备份）。",
        {"path": "工作区相对路径",
         "old": "要替换的原文",
         "new": "替换后文本"},
    ),
    "delete_file": ToolSpec(
        "delete_file",
        "删除文件（自动备份）。",
        {"path": "工作区相对路径"},
    ),
}


async def dispatch_write_tool(
    name: str, args: dict, workspace: str,
) -> dict:
    # 全部走 to_thread（磁盘 IO 不阻塞事件循环）
    try:
        if name == "write_file":
            return await asyncio.to_thread(
                _write_file,
                workspace,
                str(args.get("path", "")),
                str(args.get("content", "")),
            )
        if name == "edit_file":
            return await asyncio.to_thread(
                _edit_file,
                workspace,
                str(args.get("path", "")),
                str(args.get("old", "")),
                str(args.get("new", "")),
            )
        if name == "delete_file":
            return await asyncio.to_thread(
                _delete_file,
                workspace, str(args.get("path", "")),
            )
        return {"ok": False, "error": f"unknown write tool: {name}"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


__all__ = ["WRITE_TOOLS", "dispatch_write_tool"]
