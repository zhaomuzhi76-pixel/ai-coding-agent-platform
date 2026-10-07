"""统一 diff 生成：旧内容 → 新内容。

工业级契约：
    - 输出标准 unified diff 格式
    - 大文本走逐行对比（内存）
    - 输出 ≤ 30KB
"""
from __future__ import annotations

import difflib

_MAX_DIFF_BYTES = 30_000


def make_diff(
    path: str,
    old: str | None,
    new: str | None,
) -> str:
    old_lines = (old or "").splitlines(keepends=True)
    new_lines = (new or "").splitlines(keepends=True)
    diff_iter = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="\n",
    )
    text = "".join(diff_iter)
    if not text:
        return "(no change)"
    if len(text) > _MAX_DIFF_BYTES:
        return text[:_MAX_DIFF_BYTES] + "\n...[diff truncated]"
    return text


__all__ = ["make_diff"]
