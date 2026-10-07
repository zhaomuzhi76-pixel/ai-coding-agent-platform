"""CodeEditOrchestrator 的辅助函数。

工业级拆分：主文件只做 loop，本文件放：
  - _verify_locally      本地编译验证闸门
  - emit_file_changes    向前端推 file_change 事件
  - as_trace             把 RoleResult 转 trace
  - make_fail_result     构造失败返回
不重复职责：只做纯逻辑，不持状态。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any

from backend.agent.orchestration.contracts import RoleResult


async def verify_locally(
    *, workspace: str, changes: list,
    context: Any, verifier: Any,
) -> bool:
    """真跑编译/lint。失败则把反馈塞进 context.prior_feedback。"""
    if not workspace or not changes:
        return True
    files = []
    for c in changes:
        if not isinstance(c, dict):
            continue
        f = c.get("file") or c.get("path")
        if isinstance(f, str) and f.strip():
            files.append(f.strip())
    if not files:
        return True
    try:
        fb = verifier.verify_changes(
            workspace=workspace, files=files, timeout=20,
        )
    except Exception as e:
        print(f"[orchestrator] verify error: {e}", flush=True)
        return True
    if fb.ok:
        print(f"[orchestrator] local verify PASS ({len(files)} files)",
              flush=True)
        return True
    print(
        f"[orchestrator] local verify FAIL: {len(fb.issues)} issues",
        flush=True,
    )
    context.prior_feedback = fb.to_feedback_text()
    return False


async def emit_file_changes(
    stream_callback: Any, changes: list,
) -> None:
    """向前端发 file_change 事件（前端自动预览 diff）。"""
    if not stream_callback or not changes:
        return
    for c in changes:
        if not isinstance(c, dict):
            continue
        evt = {
            "event": "file_change",
            "file": str(c.get("file") or c.get("path") or ""),
            "kind": str(c.get("kind") or "replace"),
            "before": str(c.get("before") or ""),
            "after": str(c.get("text") or c.get("after") or ""),
        }
        if not evt["file"]:
            continue
        try:
            r = stream_callback(evt)
            if hasattr(r, "__await__"):
                await r
        except Exception as e:
            swallow("agent.orchestration.orchestrator_support:76", e)


def as_trace(result: RoleResult) -> dict[str, Any]:
    return {
        "role": result.role, "ok": result.ok,
        "data": result.data, "error": result.error,
    }


def make_fail_result(
    reason: str, trace: list[dict[str, Any]],
    error: str | None,
) -> dict[str, Any]:
    print(f"[orchestrator] FAILED reason={reason} error={error}",
          flush=True)
    return {
        "success": False, "changes": None,
        "attempts": len([t for t in trace if t["role"] == "coder"]),
        "trace": trace, "reason": reason, "error": error,
    }


__all__ = [
    "verify_locally", "emit_file_changes",
    "as_trace", "make_fail_result",
]
