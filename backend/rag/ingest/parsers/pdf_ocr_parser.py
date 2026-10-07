"""PDF OCR 解析器。职责：扫描 PDF 每页 → 渲染成图 → PaddleOCR → ParsedPage。
不做纯文本 PDF 抽取（pdf_parser 管）、不切块、不索引。
典型用法：纯文本抽取返回空时 fallback 到本解析器。
一页一处理，处理完立即删临时图（不占磁盘）。"""
from __future__ import annotations
import os
import tempfile
from typing import Any, Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)
from backend.rag.ingest.ocr.contracts import OcrResult
from backend.rag.ingest.ocr.paddle_engine import (
    PaddleOcrEngine, make_paddle_engine)

DEFAULT_DPI = 200
DEFAULT_PAGE_BATCH = 4        # 每批渲染页数（控制内存峰值）
MIN_PAGE_CHARS = 2            # 少于此字符视为空白页

class PdfOcrParser:
    def __init__(self, *, engine: Optional[Any] = None,
                 dpi: int = DEFAULT_DPI,
                 page_batch: int = DEFAULT_PAGE_BATCH,
                 max_pages: int = 0) -> None:
        if dpi <= 0:
            raise ValueError("dpi must be > 0")
        if page_batch <= 0:
            raise ValueError("page_batch must be > 0")
        if max_pages < 0:
            raise ValueError("max_pages must be >= 0")
        self._engine = engine or make_paddle_engine(lang="ch")
        self._dpi = dpi
        self._batch = page_batch
        self._max_pages = max_pages

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".pdf")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None,
              on_progress=None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        total = self._count_pages(path)
        limit = self._max_pages if self._max_pages > 0 else total
        limit = min(limit, total)

        pages: list = []
        for start in range(1, limit + 1, self._batch):
            end = min(start + self._batch - 1, limit)
            images = self._render_pages(path, start, end)
            for offset, img in enumerate(images):
                page_no = start + offset
                try:
                    text = self._ocr_image(img)
                except Exception:
                    if on_progress:
                        try: on_progress(page_no, limit)
                        except Exception: pass
                    continue
                if on_progress:
                    try: on_progress(page_no, limit)
                    except Exception: pass
                if len(text.strip()) < MIN_PAGE_CHARS:
                    continue
                pages.append(ParsedPage(text=text, page_no=page_no))
        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.PDF,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages),
            file_size=stat.st_size,
            meta={"ocr": True, "dpi": self._dpi,
                  "page_total": total,
                  "pages_with_text": len(pages),
                  **(meta or {})},
        )

    @staticmethod
    def _count_pages(path: str) -> int:
        """[ROBUST] 多层 fallback。"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(path, strict=False)
            if reader is not None:
                return len(reader.pages)
        except Exception as e:
            print(f"[count_pages] pypdf 失败: {e}", flush=True)
        try:
            import pikepdf
            with pikepdf.open(path) as pdf:
                return len(pdf.pages)
        except Exception:
            pass
        try:
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(path)
            return int(info.get("Pages", 0))
        except Exception as e:
            raise RuntimeError(f"无法读取 PDF 页数: {e}") from e

    def _render_pages(self, path: str, start: int, end: int) -> list:
        try:
            from pdf2image import convert_from_path
        except ImportError as e:
            raise RuntimeError(
                "未安装 pdf2image，请 pip install pdf2image") from e
        return convert_from_path(path, dpi=self._dpi,
                                  first_page=start, last_page=end)

    def _ocr_image(self, img: Any) -> str:
        """PIL Image → 临时 PNG → OCR → 删除临时。"""
        fd, tmp = tempfile.mkstemp(suffix=".png", prefix="pdfocr_")
        os.close(fd)
        try:
            img.save(tmp, format="PNG")
            r: OcrResult = self._engine.recognize(tmp)
            return r.text
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

def make_pdf_ocr_parser(*, lang: str = "ch", dpi: int = DEFAULT_DPI,
                        use_gpu: bool = False,
                        max_pages: int = 0) -> PdfOcrParser:
    eng = make_paddle_engine(lang=lang, use_gpu=use_gpu)
    return PdfOcrParser(engine=eng, dpi=dpi, max_pages=max_pages)

__all__ = ["PdfOcrParser", "make_pdf_ocr_parser",
           "DEFAULT_DPI", "DEFAULT_PAGE_BATCH", "MIN_PAGE_CHARS"]
