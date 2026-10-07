"""图文混合分块。职责：输入 [{text, images}] → 输出 List[MultimodalChunk]。
不向量化、不检索、不存储。与 rag/chunker.py 边界：chunker 切 JSONL 对话对；
本文件切图文块，图片挂在第一块。可注入 splitter 复用外部切分策略。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple

from backend.rag.multimodal.contracts import (
    ImageRef, MultimodalChunk, make_multimodal_chunk_id)

DEFAULT_MAX_CHARS = 800
DEFAULT_OVERLAP = 80
DEFAULT_MIN_CHARS = 20

Splitter = Callable[[str], Sequence[str]]

@dataclass(frozen=True)
class ChunkStrategy:
    max_chars: int = DEFAULT_MAX_CHARS
    overlap: int = DEFAULT_OVERLAP
    min_chars: int = DEFAULT_MIN_CHARS

    def __post_init__(self) -> None:
        if self.max_chars <= 0:
            raise ValueError("max_chars must be > 0")
        if self.overlap < 0 or self.overlap >= self.max_chars:
            raise ValueError("0 <= overlap < max_chars")
        if self.min_chars < 0:
            raise ValueError("min_chars must be >= 0")

def _hard_split(p: str, st: ChunkStrategy) -> list[str]:
    """仅对超过 max_chars 的单段做硬切；尾块过短并入上块。"""
    pieces: list[str] = []
    i = 0
    while i < len(p):
        j = min(i + st.max_chars, len(p))
        pieces.append(p[i:j])
        if j == len(p):
            break
        i = j - st.overlap
    if len(pieces) >= 2 and len(pieces[-1]) < st.min_chars:
        pieces[-2] = pieces[-2] + pieces[-1]
        pieces.pop()
    return pieces

def _default_split(text: str, st: ChunkStrategy) -> list[str]:
    """段落边界优先：每段自成一块（≤max_chars）；仅超长段做硬切。
    段落边界不合并 —— 中文短段落不应被 min_chars 误吞。"""
    text = text.strip()
    if not text:
        return []
    paras = [p.strip() for p in text.split("\n\n") if p.strip()] or [text]
    out: list[str] = []
    for p in paras:
        if len(p) <= st.max_chars:
            out.append(p)
        else:
            out.extend(_hard_split(p, st))
    return out

def _as_image_refs(raw: Any) -> Tuple[ImageRef, ...]:
    if raw is None: return ()
    if isinstance(raw, ImageRef): return (raw,)
    if isinstance(raw, Mapping): return (ImageRef.from_dict(raw),)
    if isinstance(raw, (list, tuple)):
        out: list[ImageRef] = []
        for x in raw:
            if isinstance(x, ImageRef): out.append(x)
            elif isinstance(x, Mapping): out.append(ImageRef.from_dict(x))
            else: raise TypeError(f"unsupported image entry: {type(x).__name__}")
        return tuple(out)
    raise TypeError(f"unsupported images: {type(raw).__name__}")

class MultimodalChunker:
    def __init__(self, strategy: Optional[ChunkStrategy] = None,
                 splitter: Optional[Splitter] = None) -> None:
        self._st = strategy or ChunkStrategy()
        if splitter is not None:
            self._split = lambda t: list(splitter(t))
        else:
            self._split = lambda t: _default_split(t, self._st)

    @property
    def strategy(self) -> ChunkStrategy:
        return self._st

    def chunk_text(self, text: str, *, source: str = "",
                   source_path: str = "", line_no: int = 0,
                   role: str = "", images: Any = None,
                   metadata: Optional[Mapping[str, Any]] = None
                   ) -> list[MultimodalChunk]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be non-empty str")
        img_tuple = _as_image_refs(images)
        md = dict(metadata or {})
        pieces = self._split(text)
        out: list[MultimodalChunk] = []
        for i, piece in enumerate(pieces):
            imgs = img_tuple if i == 0 else ()
            cid = make_multimodal_chunk_id(source, line_no, piece, imgs, offset=i)
            out.append(MultimodalChunk(
                chunk_id=cid, text=piece, images=imgs,
                source=source, source_path=source_path,
                line_no=line_no, role=role, metadata=md))
        return out

    def chunk_items(self, items: Iterable[Mapping[str, Any]]
                    ) -> list[MultimodalChunk]:
        out: list[MultimodalChunk] = []
        for idx, item in enumerate(items):
            if not isinstance(item, Mapping):
                raise TypeError(f"item #{idx} must be mapping")
            out.extend(self.chunk_text(
                text=str(item.get("text", "")),
                source=str(item.get("source", "")),
                source_path=str(item.get("source_path", "")),
                line_no=int(item.get("line_no", idx)),
                role=str(item.get("role", "")),
                images=item.get("images"),
                metadata=item.get("metadata") or {},
            ))
        return out

def make_default_chunker(
    strategy: Optional[ChunkStrategy] = None,
    splitter: Optional[Splitter] = None,
) -> MultimodalChunker:
    return MultimodalChunker(strategy=strategy, splitter=splitter)

__all__ = ["ChunkStrategy", "MultimodalChunker", "make_default_chunker"]
