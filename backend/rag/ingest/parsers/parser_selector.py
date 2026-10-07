"""PDF 解析器选择：smart（默认）| batch | legacy。
环境变量：
  RAG_PDF_MODE=smart   逐页智能（推荐）
  RAG_PDF_MODE=batch   批量 OCR（旧）
  RAG_PDF_MODE=legacy  单页串行
  RAG_OCR_DPI=200
  RAG_OCR_MODEL=mobile|server
"""
from __future__ import annotations
import os
from typing import Any

DEFAULT_LANG = "chinese_cht"
DEFAULT_DPI = 200
DEFAULT_MODE = "smart"


def get_pdf_ocr_parser(*, lang: str | None = None, dpi: int | None = None,
                       use_gpu: bool = False, max_pages: int = 0) -> Any:
    lang = os.environ.get("RAG_OCR_LANG") or lang or DEFAULT_LANG
    dpi = int(os.environ.get("RAG_OCR_DPI") or dpi or DEFAULT_DPI)
    mode = os.environ.get("RAG_PDF_MODE", DEFAULT_MODE).lower()

    if mode == "smart":
        try:
            from backend.rag.ingest.parsers.pdf_smart_parser_resume import (
                make_pdf_smart_parser_resume)
            print("[selector] 使用 PdfSmartParserResume（逐页 + 断点续跑）",
                  flush=True)
            return make_pdf_smart_parser_resume(lang=lang, dpi=dpi,
                                                 max_pages=max_pages)
        except Exception as e:
            print(f"[selector] smart 不可用，回退 batch: {e}", flush=True)
            mode = "batch"

    if mode == "batch":
        from backend.rag.ingest.parsers.pdf_ocr_parser_batch import (
            make_pdf_ocr_parser_batch)
        bs = int(os.environ.get("RAG_OCR_BATCH_SIZE", "2"))
        return make_pdf_ocr_parser_batch(
            lang=lang, dpi=dpi, use_gpu=use_gpu,
            max_pages=max_pages, batch_size=bs)

    from backend.rag.ingest.parsers.pdf_ocr_parser import (
        make_pdf_ocr_parser)
    return make_pdf_ocr_parser(lang=lang, dpi=dpi,
                                use_gpu=use_gpu, max_pages=max_pages)


__all__ = ["get_pdf_ocr_parser", "DEFAULT_LANG", "DEFAULT_DPI", "DEFAULT_MODE"]
