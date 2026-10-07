"""纯文本 / 日志解析器。职责：整个文件或按空行分段。
不解析编码外内容、不切块、不索引。"""
from __future__ import annotations
import os
from typing import Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)

_MAX_BYTES = 8 * 1024 * 1024  # 8MB 单文件上限，防内存爆
_SPLIT_CHARS = 4000  # 单段最大字符（长文本按此切）

class TextParser:
    def __init__(self, *, whole_file: bool = False) -> None:
        # whole_file=True → 整文件一段；False → 按空行/长度切
        self._whole = whole_file

    def supports(self, path: str) -> bool:
        p = path.lower()
        return p.endswith(".txt") or p.endswith(".log") or p.endswith(".text")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        stat = os.stat(path)
        if stat.st_size > _MAX_BYTES:
            raise ValueError(f"file too large ({stat.st_size} > {_MAX_BYTES})")
        raw = open(path, "r", encoding="utf-8", errors="replace").read()
        pages = self._split(raw)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.TEXT,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages),
            file_size=stat.st_size,
            meta={"whole_file": self._whole, **(meta or {})},
        )

    def _split(self, text: str) -> list:
        if self._whole:
            body = text.strip()
            return [ParsedPage(text=body, page_no=0)] if body else []
        # 按双换行分段；单段超长再硬切
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        out = []
        for b in blocks:
            if len(b) <= _SPLIT_CHARS:
                out.append(ParsedPage(text=b, page_no=0))
            else:
                for i in range(0, len(b), _SPLIT_CHARS):
                    piece = b[i:i + _SPLIT_CHARS].strip()
                    if piece:
                        out.append(ParsedPage(text=piece, page_no=0))
        return out

__all__ = ["TextParser"]
