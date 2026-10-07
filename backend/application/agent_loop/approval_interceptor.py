"""写操作拦截：agent_loop 调工具前先看是否需要审批。

工业级契约：
    - 写工具全部拦截（两套工具集都覆盖）：
        · agent_loop 轻量集：write_file / edit_file / delete_file / run_command
        · builtin 装配集：  file_write / file_edit
    - 命令执行工具（terminal / run_command）只读放行，写类拦截
    - 生成 PendingEdit + diff
    - 推 step 事件（type=pending_edit）
    - 挂起等批准（异步、不阻塞事件循环）
    - 沙箱三档：read-only / workspace-write / full-access
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import os
from typing import Any, Optional

from backend.workspace.file_access import WorkspaceFileAccess

from .diff_generator import make_diff
from .pending_edit import PendingEdit
from .pending_gate import get_gate

from backend.runtime.tools.security.command_guard import ToolCommandGuard

# 两套工具集的写操作名，全部拦截
_WRITE_ACTIONS = frozenset({
    # agent_loop 轻量集
    "write_file", "edit_file", "delete_file",
    # builtin 装配集
    "file_write", "file_edit",
})

# 命令执行工具（只读放行 / 写类拦截）
_TERMINAL_ACTIONS = frozenset({"terminal", "run_command"})

DEFAULT_MODE = "read-only"

_GUARD = None


def _guard():
    global _GUARD
    if _GUARD is None:
        _GUARD = ToolCommandGuard()
    return _GUARD


def _read_old(workspace: str, path: str) -> Optional[str]:
    try:
        acc = WorkspaceFileAccess(os.path.abspath(workspace))
        return acc.read_text(path)
    except Exception:
        return None


def _build_pending(action: str, args: dict, workspace: str) -> PendingEdit:
    if action in _TERMINAL_ACTIONS:
        cmd = str(args.get("command", "")).strip()
        return PendingEdit.create(
            action=action, path="[terminal]",
            old_content=None, new_content=cmd,
            diff=f"$ {cmd}\n(等待批准执行)",
        )
    path = str(args.get("path", "")).strip()
    old = _read_old(workspace, path)

    if action in ("write_file", "file_write"):
        new = str(args.get("content", ""))
    elif action in ("edit_file", "file_edit"):
        # agent_loop 用 old/new；builtin 用 old_text/new_text
        old_text = str(args.get("old", args.get("old_text", "")))
        new_text = str(args.get("new", args.get("new_text", "")))
        new = (old or "").replace(old_text, new_text, 1)
    elif action == "delete_file":
        new = None
    else:
        new = None

    diff = make_diff(path, old, new)
    return PendingEdit.create(
        action=action, path=path,
        old_content=old, new_content=new, diff=diff,
    )


async def maybe_intercept(
    action: str,
    args: dict,
    workspace: str,
    on_step: Any = None,
    mode: str = "read-only",
    tenant_id: str = "",
) -> Optional[str]:
    """若 action 是写操作，返回 decision；否则 None。

    decision ∈ {"approved", "rejected", "timeout", "unknown"}

    沙箱模式（mode）：
      read-only       — 只读命令放行；其余写操作全部审批（默认）
      workspace-write — write_file/edit_file/file_write/file_edit 直接放行；命令只读放行
      full-access     — 全部放行（保护路径由 file_access 兜底）
    """
    _VALID_MODES = frozenset({"read-only", "workspace-write", "full-access"})
    if mode not in _VALID_MODES:
        raise ValueError(f"invalid sandbox mode: {mode!r}")

    # full-access: 全部放行
    if mode == "full-access":
        return None

    # workspace-write: 写文件工具直接放行
    if mode == "workspace-write":
        if action in ("write_file", "edit_file", "file_write", "file_edit"):
            return None
        if action in _TERMINAL_ACTIONS:
            cmd = str(args.get("command", ""))
            if _guard().is_readonly(cmd, workspace):
                return None
        elif action not in _WRITE_ACTIONS:
            return None
        # 落到下面走审批

    # read-only: 只读命令放行，其余写操作全审批
    if mode == "read-only":
        if action in _TERMINAL_ACTIONS:
            cmd = str(args.get("command", ""))
            if _guard().is_readonly(cmd, workspace):
                return None
        elif action not in _WRITE_ACTIONS:
            return None

    edit = _build_pending(action, args, workspace)
    gate = get_gate()
    await gate.request(edit, tenant_id=tenant_id)

    # 推送 step 事件（前端展示 Diff Review）
    if on_step is not None:
        try:
            entry = {
                "step": -1,
                "type": "pending_edit",
                "thought": f"请求写入 {edit.path}",
                "action": action,
                "args": args,
                "observation": edit.diff[:500],
                "pending": edit.to_wire(),
            }
            res = on_step(entry)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            swallow("application.agent_loop.approval_interceptor:155", e)

    decision = await gate.wait(edit.edit_id)
    gate.cleanup(edit.edit_id)
    return decision


def write_actions() -> frozenset:
    return _WRITE_ACTIONS


__all__ = ["maybe_intercept", "write_actions", "DEFAULT_MODE"]
