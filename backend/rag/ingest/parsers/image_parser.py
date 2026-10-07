"""图片解析器。职责：图片文件 → PaddleOCR → ParsedPage。
支持 JPG / JPEG / PNG / BMP / WEBP / TIF / TIFF。
不做 PDF 渲染（pdf_ocr_parser 管）、不切块、不索引。
每种扩展名都走 OCR；engine 支持多语言。
"""
from __future__ import annotations
import os
from typing import Any, Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)
from backend.rag.ingest.ocr.paddle_engine import (
    PaddleOcrEngine, make_paddle_engine)

SUPPORTED_EXT = (
    ".jpg", ".jpeg", ".png", ".bmp",
    ".webp", ".tif", ".tiff",
)
MIN_PAGE_CHARS = 1

class ImageParser:
    def __init__(self, *, engine: Optional[Any] = None,
                 lang: str = "ch") -> None:
        self._engine = engine or make_paddle_engine(lang=lang)

    def supports(self, path: str) -> bool:
        p = path.lower()
        return any(p.endswith(ext) for ext in SUPPORTED_EXT)

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        try:
            r = self._engine.recognize(path)
        except Exception as e:
            raise RuntimeError(
                f"ImageParser OCR 失败: {type(e).__name__}: {e}") from e
        text = r.text or ""
        pages = ()
        if len(text.strip()) >= MIN_PAGE_CHARS:
            pages = (ParsedPage(text=text, page_no=1),)
        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.TEXT,  # 复用 TEXT 类型（本体是文字）
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=pages,
            file_size=stat.st_size,
            meta={"ocr": True, "image": True,
                  "line_count": len(r.lines),
                  "avg_confidence": round(r.avg_confidence, 4),
                  **(meta or {})},
        )

def make_image_parser(*, lang: str = "ch",
                      use_gpu: bool = False) -> ImageParser:
    eng = make_paddle_engine(lang=lang, use_gpu=use_gpu)
    return ImageParser(engine=eng)

__all__ = ["ImageParser", "make_image_parser", "SUPPORTED_EXT"]
