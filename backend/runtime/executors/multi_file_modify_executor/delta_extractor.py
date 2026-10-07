"""Derive a batch-safe delta from a sample before/after."""
from __future__ import annotations

import difflib
from typing import Dict


def extract_delta(before: str, after: str) -> Dict[str, object]:
    if after == before:
        raise ValueError("sample produced no change; nothing to apply")
    b_lines = before.split("\n")
    a_lines = after.split("\n")
    sm = difflib.SequenceMatcher(None, b_lines, a_lines)
    ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
    if len(ops) != 1 or ops[0][0] != "insert":
        kinds = [op[0] for op in ops]
        raise ValueError(
            f"unsafe multi-file operation: expected single insert, got {kinds}"
        )
    _, i1, i2, j1, j2 = ops[0]
    inserted = "\n".join(a_lines[j1:j2])
    common_prefix = i1
    common_suffix = len(b_lines) - i2
    if common_prefix == 0 and common_suffix > 0:
        return {"kind": "prepend", "text": inserted + "\n"}
    if common_suffix == 0 and common_prefix > 0:
        return {"kind": "append", "text": "\n" + inserted}
    if common_prefix == 0 and common_suffix == 0:
        return {"kind": "prepend", "text": inserted + "\n"}
    return {
        "kind": "insert_after_line",
        "after_line": common_prefix,
        "text": inserted,
    }

DEFAULT_CHUNK_LINES = 500


def extract_line_chunks(
    before: str,
    after: str,
    *,
    file: str = "",
    max_lines: int = DEFAULT_CHUNK_LINES,
    semantic_unit: str = "",
) -> list[dict]:
    """把 before/after 差异切成"行区间"chunks（供大文件分页 + 语义分组）。

    与 extract_delta 的区别：
        - extract_delta 返回单点操作（insert/prepend/append）
        - extract_line_chunks 返回"行区间"（支持任意大小文件）
    两者职责不同，不重复。

    返回 list[dict]，每项形如：
        {"file", "start_line", "end_line", "before", "after",
         "semantic_unit", "line_span"}
    """
    if max_lines <= 0:
        max_lines = DEFAULT_CHUNK_LINES
    b_lines = before.split("\n") if before else []
    a_lines = after.split("\n") if after else []
    total = max(len(b_lines), len(a_lines))
    if total == 0:
        return [{
            "file": file, "start_line": 1, "end_line": 0,
            "before": "", "after": "",
            "semantic_unit": semantic_unit, "line_span": 0,
        }]
    out: list[dict] = []
    i = 0
    while i < total:
        end = min(i + max_lines, total)
        b = "\n".join(b_lines[i:end]) if b_lines else ""
        a = "\n".join(a_lines[i:end]) if a_lines else ""
        out.append({
            "file": file,
            "start_line": i + 1,
            "end_line": end,
            "before": b,
            "after": a,
            "semantic_unit": semantic_unit,
            "line_span": end - i,
        })
        i = end
    return out


def group_by_semantic_unit(chunks: list) -> dict:
    """按 semantic_unit 分组（供前端折叠）。空值归到 "(未分组)"。"""
    out: dict = {}
    for c in chunks or ():
        if not isinstance(c, dict):
            continue
        key = str(c.get("semantic_unit", "") or "") or "(未分组)"
        out.setdefault(key, []).append(c)
    return out


__all__ = ["extract_delta", "extract_line_chunks", "group_by_semantic_unit",
           "DEFAULT_CHUNK_LINES"]
