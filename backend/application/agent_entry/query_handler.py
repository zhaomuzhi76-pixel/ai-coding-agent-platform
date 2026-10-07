"""只读查询：文件数、目录统计。

不调 LLM，直接遍历文件系统；命中即返回结构化结果 + 步骤 trace。

工业级契约：
  - async：on_step 可能是 async 回调，必须 await
  - 不阻塞事件循环
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import os
import re
from typing import Any, Awaitable, Callable, Optional, Union

from backend.application._common.file_walk import walk_files
from backend.workspace.workspace_path import normalize_only


OnStep = Union[
    Callable[[dict], None],
    Callable[[dict], Awaitable[None]],
]


def _extract_ext(message: str) -> str | None:
    m = re.search(
        r"\b(py|ts|tsx|js|jsx|go|rs|java|rb|php|c|cpp|cs|md|ya?ml)\b",
        message, re.IGNORECASE,
    )
    return "." + m.group(1).lower() if m else None


async def _fire_step(
    trace: list[dict[str, Any]],
    on_step: Optional[OnStep],
    *,
    thought: str,
    action: str,
    args: dict[str, Any],
    observation: str,
    remaining: int = 0,
) -> None:
    import time as _time
    entry = {
        "step": len(trace) + 1,
        "thought": thought,
        "action": action,
        "args": args,
        "observation": observation,
        "remaining": remaining,
        "ts_ms": int(_time.time() * 1000),
    }
    trace.append(entry)
    if on_step is None:
        return
    try:
        result = on_step(entry)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:
        swallow("application.agent_entry.query_handler:63", e)


async def handle_query(
    message: str,
    workspace: str,
    on_step: Optional[OnStep] = None,
) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []

    # 步骤 1：解析 workspace
    root = normalize_only(workspace or "")
    await _fire_step(
        trace, on_step,
        thought=f"检查工作区 {root or '(空)'}",
        action="resolve_workspace",
        args={"workspace": workspace},
        observation=f"解析后 root={root!r}",
    )

    if not root or not os.path.isdir(root):
        return {
            "success": False,
            "error": f"workspace not found: {workspace!r}",
            "trace": trace,
        }

    # 步骤 2：扫描目录（走 to_thread 避免阻塞事件循环）
    def _scan(root_dir: str):
        by_ext: dict[str, int] = {}
        total = 0
        for rel, _ in walk_files(root_dir):
            total += 1
            _, ext = os.path.splitext(rel)
            if ext:
                k = ext.lower()
                by_ext[k] = by_ext.get(k, 0) + 1
        return by_ext, total

    by_ext, total = await asyncio.to_thread(_scan, root)

    want_ext = _extract_ext(message)
    await _fire_step(
        trace, on_step,
        thought=f"扫描目录并统计扩展名（目标扩展名={want_ext or '(全部)'}）",
        action="scan_tree",
        args={"root": root, "target_ext": want_ext or ""},
        observation=f"发现 {total} 个文件，涉及 {len(by_ext)} 种扩展名",
    )

    if want_ext:
        n = by_ext.get(want_ext, 0)
        await _fire_step(
            trace, on_step,
            thought=f"统计 {want_ext} 文件",
            action="count_by_ext",
            args={"ext": want_ext},
            observation=f"命中 {n} 个 {want_ext} 文件",
        )
        return {
            "success": True,
            "kind": "count",
            "workspace": root,
            "ext": want_ext,
            "count": n,
            "total_files": total,
            "trace": trace,
            "text": f"{root} 下有 {n} 个 {want_ext} 文件（共 {total} 个文件）",
        }

    top = sorted(by_ext.items(), key=lambda x: -x[1])[:8]
    summary = "、".join(f"{e}×{n}" for e, n in top) or "无扩展名统计"

    await _fire_step(
        trace, on_step,
        thought="汇总扩展名分布",
        action="summarize",
        args={"top": len(top)},
        observation=summary,
    )

    return {
        "success": True,
        "kind": "summary",
        "workspace": root,
        "total_files": total,
        "by_ext": dict(top),
        "trace": trace,
        "text": f"{root} 下共 {total} 个文件（{summary}）",
    }


__all__ = ["handle_query"]
