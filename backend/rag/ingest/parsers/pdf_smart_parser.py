"""PDF 逐页智能解析器：文本优先，扫描页走 OCR。
每页独立判断：
  文本 >= 30 字符 → 用 pypdf 文本（0.01s/页）
  文本 < 30 字符 → 渲染 + OCR（GPU 0.5s/页）
混合 PDF 最优。
"""
from __future__ import annotations
import os
import tempfile
from typing import Any, List, Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)

DEFAULT_MIN_TEXT = 30
DEFAULT_DPI = 200


class PdfSmartParser:
    def __init__(self, *, engine: Any = None, dpi: int = DEFAULT_DPI,
                 min_text: int = DEFAULT_MIN_TEXT, max_pages: int = 0):
        if engine is None:
            from backend.rag.ingest.ocr.batch_engine import make_batch_engine
            engine = make_batch_engine(lang="ch")
        self._engine = engine
        self._dpi = dpi
        self._min_text = min_text
        self._max_pages = max_pages

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".pdf")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None,
              on_progress=None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        # [GPU-AUTO] 请求独占 GPU
        from backend.rag.ingest.ocr.gpu_coordinator import (
            acquire as _gpu_acq, release as _gpu_rel)
        import logging as _lg
        _need = 1500 if os.environ.get("RAG_OCR_MODEL", "mobile") == "mobile" else 3500
        _got = _gpu_acq("ocr", need_mb=_need)

        try:
            return self._do_parse(path, title, meta, on_progress)
        finally:
            try:
                import gc as _gc
                _gc.collect()
                try:
                    import paddle
                    paddle.device.cuda.empty_cache()
                    _lg.getLogger(__name__).info("[smart-pdf] Paddle 显存已清空")
                except Exception:
                    pass
                _gpu_rel("ocr")
                _lg.getLogger(__name__).info("[smart-pdf] GPU 已释放")
            except Exception:
                pass

    def _do_parse(self, path, title, meta, on_progress):
        from pypdf import PdfReader
        reader = PdfReader(path, strict=False)
        total = len(reader.pages)
        limit = self._max_pages if self._max_pages > 0 else total
        limit = min(limit, total)

        text_pages: List[ParsedPage] = []
        ocr_needed: List[int] = []

        for i in range(limit):
            try:
                t = (reader.pages[i].extract_text() or "").strip()
            except Exception:
                t = ""
            if len(t) >= self._min_text:
                text_pages.append(ParsedPage(text=t, page_no=i + 1))
            else:
                ocr_needed.append(i + 1)

        print(f"[smart-pdf] 文本页={len(text_pages)} 扫描页={len(ocr_needed)} 共{limit}",
              flush=True)

        # 全部文本 → 秒返回
        if not ocr_needed:
            if on_progress:
                try: on_progress(limit, limit)
                except Exception: pass
            return self._build(path, title, meta, text_pages, total, limit)

        # 部分/全部扫描 → 只 OCR 需要页
        ocr_pages = self._ocr_pages(path, ocr_needed, limit,
                                     len(text_pages), on_progress)
        all_pages = sorted(text_pages + ocr_pages, key=lambda p: p.page_no)
        return self._build(path, title, meta, all_pages, total, limit)

    def _ocr_pages(self, path, page_nos, limit, done_offset, on_progress):
        from pdf2image import convert_from_path
        try:
            from backend.rag.ingest.ocr.tcm_corrections import correct as _corr
        except Exception:
            _corr = lambda x: x

        out = []
        tmp_dir = tempfile.mkdtemp(prefix="pdfsmart_")
        processed = 0
        try:
            for start, end in self._group(page_nos, max_span=10):
                try:
                    imgs = convert_from_path(
                        path, dpi=self._dpi,
                        first_page=start, last_page=end)
                except Exception as e:
                    print(f"[smart-pdf] 渲染 {start}-{end} 失败: {e}", flush=True)
                    continue
                paths = []
                try:
                    for img in imgs:
                        fd, tmp = tempfile.mkstemp(
                            suffix=".png", prefix="p_", dir=tmp_dir)
                        os.close(fd)
                        img.save(tmp, "PNG")
                        paths.append(tmp)
                    results = self._engine.recognize_batch(paths)
                    for pn, r in zip(range(start, end + 1), results):
                        txt = getattr(r, "text", "") or ""
                        try: txt = _corr(txt)
                        except Exception: pass
                        if txt.strip():
                            out.append(ParsedPage(text=txt, page_no=pn))
                        processed += 1
                        if on_progress:
                            try:
                                on_progress(done_offset + processed, limit)
                            except Exception: pass
                finally:
                    for p in paths:
                        try: os.unlink(p)
                        except OSError: pass
                    for img in imgs:
                        try: img.close()
                        except Exception: pass
                    imgs.clear()
                    import gc as _gc
                    _gc.collect()
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return out

    @staticmethod
    def _group(pages, max_span: int = 10):
        """[FIX] 连续页码分组 ≤max_span 页/组（默认 10）。"""
        if not pages: return []
        s = sorted(pages)
        groups = []
        start = prev = s[0]
        for p in s[1:]:
            if p == prev + 1 and (prev + 1 - start) < max_span:
                prev = p
            else:
                groups.append((start, prev))
                start = prev = p
        groups.append((start, prev))
        return groups

    def _build(self, path, title, meta, pages, total, limit):
        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.PDF,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages),
            file_size=stat.st_size,
            meta={"ocr": True, "dpi": self._dpi,
                  "page_total": total, "pages_with_text": len(pages),
                  "smart_mode": True, **(meta or {})},
        )


def make_pdf_smart_parser(*, lang: str = "ch", dpi: int = DEFAULT_DPI,
                          max_pages: int = 0):
    from backend.rag.ingest.ocr.batch_engine import make_batch_engine
    eng = make_batch_engine(lang=lang)
    return PdfSmartParser(engine=eng, dpi=dpi, max_pages=max_pages)


__all__ = ["PdfSmartParser", "make_pdf_smart_parser",
           "DEFAULT_MIN_TEXT", "DEFAULT_DPI"]
