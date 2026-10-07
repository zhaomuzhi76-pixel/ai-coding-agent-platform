"""LLM change → PatchExecutor patch 适配。

LLM 返回：
    {file, kind:"replace_all|prepend|append", text}              ← 整文件
    {file, kind:"edit", edits:[{old, new}, ...]}                 ← 局部编辑

PatchExecutor 需要：
    {"file", "operation":"replace", "old_content", "replacement",
     "reason", "risk"}
"""
from __future__ import annotations

import os
from typing import Any, Dict, List


def _apply_edits(old_content: str, edits: list) -> str:
    """逐条 old→new 替换（只替换首次出现）。返回新内容。"""
    modified = old_content
    for e in edits or []:
        if not isinstance(e, dict):
            continue
        old_frag = e.get("old") or e.get("old_text") or e.get("search") or ""
        new_frag = e.get("new") or e.get("new_text") or e.get("replace") or ""
        if not isinstance(old_frag, str) or not old_frag:
            continue
        if not isinstance(new_frag, str):
            new_frag = ""
        if old_frag in modified:
            modified = modified.replace(old_frag, new_frag, 1)
        else:
            print(
                f"[change_to_patch] edit fragment not found: "
                f"{old_frag[:80]!r}",
                flush=True,
            )
    return modified


def change_to_patch(
    change: Dict[str, Any],
    workspace: str,
) -> Dict[str, Any]:
    file = str(change.get("file", "")).strip()
    if not file:
        raise ValueError(f"invalid change (file required): {change}")

    full = (
        file if os.path.isabs(file)
        else os.path.join(workspace, file)
    )
    # 工业级：文件不存在 → 新建文件（old_content 为空）
    if os.path.isfile(full):
        with open(full, "r", encoding="utf-8") as fh:
            old_content = fh.read()
        is_new_file = False
    else:
        old_content = ""
        is_new_file = True
        print(
            f"[change_to_patch] new file mode: {file}",
            flush=True,
        )

    kind = str(change.get("kind", "")).strip()
    # 新建文件统一用 replace_all（old_content 已为空）
    if kind == "create":
        kind = "replace_all"

    # ── edit 模式（局部替换，工业级大文件方案）──
    if kind == "edit" and is_new_file:
        # 新建文件不能用 edit（无旧内容），转 replace_all
        print(
            f"[change_to_patch] new file + edit → replace_all: {file}",
            flush=True,
        )
        text = change.get("text", "")
        # 从 edits 里拼 new 内容
        if not text:
            edits = change.get("edits") or []
            text = "".join(
                e.get("new", "") for e in edits if isinstance(e, dict)
            )
        change = dict(change)
        change["kind"] = "replace_all"
        change["text"] = text
        kind = "replace_all"

    if kind == "edit":
        edits = change.get("edits") or []
        if not isinstance(edits, list) or not edits:
            raise ValueError(
                f"edit mode requires non-empty edits list: {file}"
            )
        replacement = _apply_edits(old_content, edits)
        if replacement == old_content:
            raise ValueError(
                f"edit produced no change (no fragment matched): {file}"
            )
    # ── 传统整文件模式 ──
    elif kind:
        text = change.get("text", "")
        if not isinstance(text, str):
            raise TypeError(f"change.text must str: {file}")
        if kind == "replace_all":
            replacement = text
        elif kind == "prepend":
            replacement = text + old_content
        elif kind == "append":
            replacement = old_content + text
        else:
            raise ValueError(f"unsupported kind: {kind}")
    elif "before" in change or "after" in change:
        after = change.get("after", change.get("new", ""))
        if not isinstance(after, str):
            raise TypeError(f"change.after must str: {file}")
        replacement = after
    else:
        raise ValueError(f"invalid change (no kind, no before/after): {change}")

    return {
        "file": file,
        "operation": "replace",
        "old_content": old_content,
        "replacement": replacement,
        "reason": str(change.get("reason", "")),
        "risk": "review",
    }


def changes_to_patches(
    changes: List[Dict[str, Any]],
    workspace: str,
) -> List[Dict[str, Any]]:
    return [change_to_patch(c, workspace) for c in changes]


__all__ = ["change_to_patch", "changes_to_patches"]
