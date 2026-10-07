"""轻量只读工具集：服务 WS Agent 循环。

工业级契约：
  1. 只读 — 永不修改 workspace
  2. 实时 — 直接读文件系统，不走索引
  3. 无装配 — 只需 workspace_root

与 backend/tools/builtin/ 的边界：
  - builtin/FileReadTool  : 走 WorkspaceOperationContract，需全套装配
  - 本模块 read_file      : 复用 WorkspaceFileAccess（轻量、实时）
  - builtin/SearchTool    : 走索引，非实时
  - 本模块 grep           : 实时递归扫描
"""
from __future__ import annotations

import asyncio

import os

from backend.application._common.file_walk import walk_files
from backend.workspace.file_access import WorkspaceFileAccess
from backend.workspace.path_normalizer import normalize_workspace_path

from .tool_spec import ToolSpec
from ._shared import get_access
from .write_tools import WRITE_TOOLS, dispatch_write_tool
from .run_command_tool import RUN_COMMAND_TOOL, dispatch_run_command
from .stat_tool import FILE_STAT_TOOL, dispatch_file_stat

_MAX_READ_BYTES = 200_000
_MAX_GREP_HITS = 50
_MAX_LIST_ENTRIES = 200
def _read_file(workspace: str, path: str) -> dict:
    try:
        content = get_access(workspace).read_text(path)
    except PermissionError as exc:
        return {"ok": False, "error": f"path traversal: {exc}", "path": path}
    except FileNotFoundError:
        return {"ok": False, "error": f"file not found: {path}", "path": path}
    except IsADirectoryError:
        return {"ok": False, "error": f"not a file: {path}", "path": path}
    except (OSError, UnicodeDecodeError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "path": path}
    if len(content) > _MAX_READ_BYTES:
        return {"ok": False, "error": f"file too large ({len(content)} chars)", "path": path}
    return {"ok": True, "path": path, "size": len(content), "content": content}


def _list_dir(workspace: str, path: str = ".") -> dict:
    root = normalize_workspace_path(workspace)
    target = normalize_workspace_path(
        path if os.path.isabs(path) else os.path.join(root, path)
    )
    if not os.path.isdir(target):
        return {"ok": False, "error": f"not a directory: {path}"}
    entries: list[str] = []
    for name in sorted(os.listdir(target)):
        if name.startswith(".git"):
            continue
        if name in ("__pycache__", "node_modules"):
            continue
        full = os.path.join(target, name)
        entries.append(name + ("/" if os.path.isdir(full) else ""))
        if len(entries) >= _MAX_LIST_ENTRIES:
            entries.append("...(truncated)")
            break
    return {"ok": True, "path": path, "entries": entries}


def _grep(workspace: str, pattern: str, ext: str = "") -> dict:
    hits: list[str] = []
    for rel, full in walk_files(workspace):
        if ext and not rel.endswith(ext):
            continue
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if pattern in line:
                        hits.append(f"{rel}:{i}: {line.rstrip()[:200]}")
                        if len(hits) >= _MAX_GREP_HITS:
                            break
        except (OSError, UnicodeDecodeError):
            continue
        if len(hits) >= _MAX_GREP_HITS:
            break
    return {"ok": True, "pattern": pattern, "hits": hits,
            "count": len(hits), "truncated": len(hits) >= _MAX_GREP_HITS}


def _count_files(workspace: str, ext: str = "") -> dict:
    total = matched = 0
    for rel, _ in walk_files(workspace):
        total += 1
        if ext and rel.endswith(ext):
            matched += 1
    return {"ok": True, "ext": ext, "matched": matched, "total": total}


_TOOLS = {
    "read_file": ToolSpec(
        "read_file", "读取 workspace 内文件内容。",
        {"path": "工作区相对路径（如 src/main.py）"},
    ),
    "list_dir": ToolSpec(
        "list_dir", "列出目录内容。",
        {"path": "工作区相对路径（默认 .）"},
    ),
    "grep": ToolSpec(
        "grep", "在工作区文件中搜索字符串。",
        {"pattern": "要搜索的字符串", "ext": "可选，仅搜索此扩展名（如 .py）"},
    ),
    "count_files": ToolSpec(
        "count_files", "统计工作区文件数。",
        {"ext": "可选，仅统计此扩展名（如 .py）"},
    ),
}


def specs() -> list[ToolSpec]:
    return (
        list(_TOOLS.values())
        + list(WRITE_TOOLS.values())
        + [RUN_COMMAND_TOOL, FILE_STAT_TOOL]
    )


async def dispatch_tool(name: str, args: dict, workspace: str,
                         domains: list | None = None) -> dict:
    # 领域约束：拦截越权调用（只有 domain_* 类工具）
    if domains and name.startswith("domain_"):
        _d = str(args.get("domain", "") or "").strip()
        if _d and _d not in domains:
            return {"ok": False,
                    "error": (
                        f"domain '{_d}' 未在授权清单内。"
                        f"允许的领域：{domains}"
                    )}
    # 写工具先分流（独立插件）
    if name in WRITE_TOOLS:
        return await dispatch_write_tool(name, args, workspace)
    # 命令执行工具分流
    if name == "run_command":
        return await dispatch_run_command(name, args, workspace)
    # 只读工具走 to_thread（避免同步 IO 阻塞事件循环）
    try:
        if name == "read_file":
            return await asyncio.to_thread(
                _read_file, workspace, str(args.get("path", "")),
            )
        if name == "list_dir":
            return await asyncio.to_thread(
                _list_dir, workspace, str(args.get("path", ".")),
            )
        if name == "grep":
            return await asyncio.to_thread(
                _grep, workspace,
                str(args.get("pattern", "")),
                str(args.get("ext", "") or ""),
            )
        if name == "count_files":
            return await asyncio.to_thread(
                _count_files, workspace,
                str(args.get("ext", "") or ""),
            )
        if name == "file_stat":
            return await asyncio.to_thread(
                dispatch_file_stat, args, workspace,
            )
        return {"ok": False, "error": f"unknown tool: {name}"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


__all__ = ["specs", "dispatch_tool"]
