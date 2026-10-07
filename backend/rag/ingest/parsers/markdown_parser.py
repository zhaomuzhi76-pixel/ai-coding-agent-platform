"""Markdown 解析器。职责：按 # 标题切段，每段作为一页（page_no=0）。
不处理内嵌图片（后续可扩展）、不切块、不索引。
"""
from __future__ import annotations
import os
import re
from typing import Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

class MarkdownParser:
    def supports(self, path: str) -> bool:
        p = path.lower()
        return p.endswith(".md") or p.endswith(".markdown")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        raw = open(path, "r", encoding="utf-8", errors="replace").read()
        pages = self._split_by_headings(raw)
        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.MARKDOWN,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages),
            file_size=stat.st_size,
            meta={"section_count": len(pages), **(meta or {})},
        )

    @staticmethod
    def _split_by_headings(text: str) -> list:
        out = []
        matches = list(_HEADING_RE.finditer(text))
        if not matches:
            body = text.strip()
            if body:
                out.append(ParsedPage(text=body, page_no=0, section=""))
            return out
        # 标题前的内容（如有）
        head = text[:matches[0].start()].strip()
        if head:
            out.append(ParsedPage(text=head, page_no=0, section=""))
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            section = m.group(2).strip()
            if body:
                out.append(ParsedPage(text=body, page_no=0, section=section))
        return out

__all__ = ["MarkdownParser"]
