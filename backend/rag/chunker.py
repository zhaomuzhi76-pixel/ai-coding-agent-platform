"""文本切片（L0 · 纯函数）。

职责：
    - 固定窗口 + 重叠切片
    - 尊重段落边界（尽量不断句）

不负责：
    - 向量化 / 存储 / 检索
"""
from __future__ import annotations

from typing import Iterable

from .spec import RagChunk, make_chunk_id

DEFAULT_CHUNK_CHARS = 800
DEFAULT_OVERLAP_CHARS = 100


def _clean(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in t.split("\n")]
    return "\n".join(lines).strip()


def chunk_text(
    text: str,
    *,
    source: str = "",
    source_path: str = "",
    line_no: int = 0,
    role: str = "",
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[RagChunk]:
    """把长文本切成 chunks（滑窗 + 重叠）。

    - 空文本 → 返回 []
    - 短文本 → 单 chunk
    - 长文本 → 按 chunk_chars 切，相邻 chunk 重叠 overlap_chars
    """
    cleaned = _clean(text)
    if not cleaned:
        return []

    if chunk_chars <= 0:
        chunk_chars = DEFAULT_CHUNK_CHARS
    if overlap_chars < 0:
        overlap_chars = 0
    if overlap_chars >= chunk_chars:
        overlap_chars = max(0, chunk_chars // 4)

    if len(cleaned) <= chunk_chars:
        cid = make_chunk_id(source, line_no, 0, cleaned)
        return [RagChunk(
            chunk_id=cid, text=cleaned, source=source,
            source_path=source_path, line_no=line_no, role=role,
        )]

    out: list[RagChunk] = []
    step = chunk_chars - overlap_chars
    i = 0
    while i < len(cleaned):
        seg = cleaned[i:i + chunk_chars]
        # 尝试在段落边界切（找不到则原样切）
        if len(seg) == chunk_chars and i + chunk_chars < len(cleaned):
            cut = seg.rfind("\n\n")
            if cut > chunk_chars // 2:
                seg = seg[:cut]
        seg = seg.strip()
        if seg:
            cid = make_chunk_id(source, line_no, i, seg)
            out.append(RagChunk(
                chunk_id=cid, text=seg, source=source,
                source_path=source_path, line_no=line_no, role=role,
            ))
        i += step
        if len(cleaned) - i < overlap_chars:
            break
    return out


def chunk_pair(
    user_text: str,
    assistant_text: str,
    *,
    source: str = "",
    source_path: str = "",
    line_no: int = 0,
) -> list[RagChunk]:
    """微调数据集 {user, assistant} 一行 → chunks。

    策略：把 user + assistant 合并成一个对话片段切片，
    用 role="qa" 标记，方便过滤。
    """
    combined = f"Q: {user_text.strip()}\nA: {assistant_text.strip()}"
    return chunk_text(
        combined, source=source, source_path=source_path,
        line_no=line_no, role="qa",
    )


def chunk_many(
    items: Iterable[dict],
    *,
    source: str = "",
    source_path: str = "",
) -> list[RagChunk]:
    """一批 {user, assistant} → chunks（带行号）。"""
    out: list[RagChunk] = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            continue
        u = str(it.get("user", it.get("instruction", "")) or "")
        a = str(it.get("assistant", it.get("output", "")) or "")
        if not u or not a:
            continue
        out.extend(chunk_pair(
            u, a, source=source, source_path=source_path, line_no=i,
        ))
    return out


__all__ = [
    "chunk_text", "chunk_pair", "chunk_many",
    "DEFAULT_CHUNK_CHARS", "DEFAULT_OVERLAP_CHARS",
]
