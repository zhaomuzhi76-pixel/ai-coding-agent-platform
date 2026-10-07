"""PDF 解析器。职责：pypdf 抽每页文本 → ParsedPage。
不切块（chunker 管）、不索引（indexer 管）、不做 OCR。
扫描图 PDF 会退化为空文本 — 用户需先做 OCR 转换。"""
from __future__ import annotations
import os
from typing import Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)

_MIN_PAGE_CHARS = 4  # 少于 4 字符视为空白页

class PdfParser:
    """依赖 pypdf。缺包时 supports() 仍返回 True；parse() 会抛错。"""
    def __init__(self, *, max_pages: int = 0) -> None:
        self._max_pages = max_pages  # 0 = 不限

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".pdf")

    def parse(self, path: str, on_progress=None, *, title: str = "",
              meta: Optional[dict] = None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise RuntimeError("未安装 pypdf，请 pip install pypdf") from e

        reader = PdfReader(path)
        pages = []
        limit = self._max_pages if self._max_pages > 0 else len(reader.pages)
        for i, page in enumerate(reader.pages[:limit]):
            try:
                txt = (page.extract_text() or "").strip()
            except Exception:
                txt = ""
            if len(txt) < _MIN_PAGE_CHARS:
                continue
            pages.append(ParsedPage(text=txt, page_no=i + 1))
        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.PDF,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages),
            file_size=stat.st_size,
            meta={"page_total": len(reader.pages),
                  "pages_with_text": len(pages),
                  **(meta or {})},
        )

__all__ = ["PdfParser"]
