"""解析器分发。职责：按路径选合适 parser 并执行；PDF 抽不到文字时自动切 OCR。
不做索引、不落盘、不做切片。规则：第一个 supports() 返回 True 者胜出。
PDF 特例：先试文本抽取，若无文字则自动切 PDF-OCR。
"""
from __future__ import annotations
from typing import Optional, Sequence

from backend.rag.ingest.contracts import SourceDocument, detect_source_type
from backend.rag.ingest.ocr.engine_pool import (
    DEFAULT_LANG, OcrEnginePool, get_default_pool)
from backend.rag.ingest.parsers.pdf_parser import PdfParser
from .quality import is_garbled, quality_score
from backend.rag.ingest.parsers.markdown_parser import MarkdownParser
from backend.rag.ingest.parsers.text_parser import TextParser
from backend.rag.ingest.parsers.image_parser import ImageParser
from backend.rag.ingest.parsers.docx_parser import DocxParser
from backend.rag.ingest.parsers.xlsx_parser import XlsxParser
from backend.rag.ingest.parsers.pptx_parser import PptxParser
from backend.rag.ingest.parsers.html_parser import HtmlParser

DEFAULT_MIN_PDF_CHARS = 20  # 少于此字符视为"无文字层"

class ParserDispatcher:
    """支持 auto_ocr：PDF 抽不到文字时自动 fallback 到 PDF-OCR。
    无 OCR 依赖时（paddleocr 未装）静默降级为纯文本。"""
    def __init__(self, parsers: Optional[Sequence] = None,
                 *,
                 auto_ocr: bool = True,
                 min_pdf_chars: int = DEFAULT_MIN_PDF_CHARS,
                 pdf_ocr_parser: Optional[object] = None,
                 lang: str = DEFAULT_LANG,
                 pool: Optional[OcrEnginePool] = None) -> None:
        if min_pdf_chars < 0:
            raise ValueError("min_pdf_chars must be >= 0")
        self._auto_ocr = auto_ocr
        self._min_chars = min_pdf_chars
        self._lang = lang
        self._pool = pool or get_default_pool()
        # ImageParser 用 pool 里对应语言的 engine
        img = ImageParser(engine=self._pool.get(lang))
        self._parsers = tuple(parsers) if parsers else (
            PdfParser(), ImageParser(engine=self._pool.get(lang)),
            MarkdownParser(), TextParser(),
            DocxParser(), XlsxParser(), PptxParser(), HtmlParser(),
        )
        self._pdf_ocr = pdf_ocr_parser  # 懒加载

    def _find_pdf_parser(self):
        """从 _parsers 里找 PdfParser 实例。"""
        from .pdf_parser import PdfParser
        for p in self._parsers:
            if isinstance(p, PdfParser):
                return p
        # 兜底：新建一个
        return PdfParser()

    def parsers(self) -> tuple:
        return self._parsers

    def supports(self, path: str) -> bool:
        return any(p.supports(path) for p in self._parsers)

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None,
              on_progress=None) -> SourceDocument:
        st = detect_source_type(path)
        if st.value == "pdf" and self._auto_ocr:
            return self._parse_pdf_with_ocr_fallback(path, title, meta,
                                                       on_progress=on_progress)
        for p in self._parsers:
            if p.supports(path):
                return p.parse(path, title=title, meta=meta)
        raise ValueError(f"无解析器处理: {path}（类型 {st.value}）")

    # ---------- 内部 ----------
    def _parse_pdf_with_ocr_fallback(self, path: str, title: str = "",
                                      meta: Optional[dict] = None,
                                      on_progress: Any = None) -> Any:
        """PDF 解析：先文字抽取 + 质量检测 → 乱码则切 OCR。"""
        import os as _os
        # 强制 OCR 模式
        if _os.environ.get("RAG_FORCE_OCR") == "1":
            print("[dispatcher] FORCE_OCR 模式，直接走 PaddleOCR", flush=True)
            return self._run_ocr(path, title, meta, on_progress)

        # 1. 文字抽取
        result = None
        full_text = ""
        try:
            result = self._find_pdf_parser().parse(path, title=title,
                                            meta=meta,
                                            on_progress=on_progress)
            pages = list(getattr(result, "pages", ()) or ())
            full_text = "\n".join(
                str(getattr(pg, "text", "") or "") for pg in pages)
        except Exception as e:
            print(f"[dispatcher] text parse failed: {e}", flush=True)

        # 2. 质量检测
        garbled, reason = is_garbled(full_text)
        q_score = quality_score(full_text)
        print(f"[dispatcher] text_len={len(full_text)} "
              f"quality={q_score} garbled={garbled} reason={reason}",
              flush=True)

        if not garbled and full_text.strip():
            return result  # 干净 → 直接用

        # 3. 乱码 → OCR
        print(f"[dispatcher] 检测到低质量内容({reason})，切换 PaddleOCR",
              flush=True)
        try:
            ocr_result = self._run_ocr(path, title, meta, on_progress)
            ocr_pages = list(getattr(ocr_result, "pages", ()) or ())
            if ocr_pages:
                ocr_text = "\n".join(
                    str(getattr(pg, "text", "") or "") for pg in ocr_pages)
                print(f"[dispatcher] OCR 完成 text_len={len(ocr_text)}",
                      flush=True)
                return ocr_result
            print("[dispatcher] OCR 无输出，保留原结果", flush=True)
        except Exception as e:
            print(f"[dispatcher] OCR 失败: {type(e).__name__}: {e}",
                  flush=True)
        return result

    def _run_ocr(self, path: str, title: str = "",
                 meta: Optional[dict] = None,
                 on_progress: Any = None) -> Any:
        """懒加载 PDF-OCR parser 并执行。"""
        if self._pdf_ocr is None:
            # [V9] 通过 selector 选择批量/单页（RAG_OCR_BATCH 环境变量控制）
            from backend.rag.ingest.parsers.parser_selector import (
                get_pdf_ocr_parser)
            self._pdf_ocr = get_pdf_ocr_parser(lang=self._lang)
        return self._pdf_ocr.parse(path, title=title, meta=meta,
                                   on_progress=on_progress)

    def _ensure_ocr(self):
        if not self._auto_ocr:
            return None
        if self._pdf_ocr is not None:
            return self._pdf_ocr
        try:
            from backend.rag.ingest.parsers.pdf_ocr_parser import (
                PdfOcrParser)
            engine = self._pool.get(self._lang)
            self._pdf_ocr = PdfOcrParser(engine=engine)
        except Exception:
            self._pdf_ocr = None
        return self._pdf_ocr


def _empty_doc(path: str, title: str) -> SourceDocument:
    import os
    return SourceDocument(
        path=os.path.abspath(path), source_type=detect_source_type(path),
        title=title or os.path.basename(path), pages=(),
        meta={"empty": True})


_DEFAULT: Optional[ParserDispatcher] = None


def get_default_dispatcher() -> ParserDispatcher:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = ParserDispatcher(auto_ocr=True, lang=DEFAULT_LANG)
    return _DEFAULT


__all__ = ["ParserDispatcher", "get_default_dispatcher",
           "DEFAULT_MIN_PDF_CHARS"]
