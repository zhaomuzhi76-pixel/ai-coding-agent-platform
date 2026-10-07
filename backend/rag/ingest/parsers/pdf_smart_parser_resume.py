"""支持 start_page 的 PdfSmartParser：用于断点续跑。
继承原 PdfSmartParser，重写 parse 逻辑：
  1. 从 start_page 页开始（跳过已 OCR）
  2. 每页 OCR 完立刻写 OcrCheckpoint
  3. 崩溃后从 checkpoint 读回已完成页 + 从 next_page 继续
"""
from __future__ import annotations
import os
from typing import Any, List, Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)
from backend.rag.ingest.parsers.pdf_smart_parser import (
    PdfSmartParser, DEFAULT_MIN_TEXT, DEFAULT_DPI)


class PdfSmartParserResume(PdfSmartParser):
    """在 PdfSmartParser 之上加断点续跑能力。"""

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None,
              on_progress=None) -> SourceDocument:
        job_id = (meta or {}).get("job_id", "")
        if not job_id:
            # 无 job_id → 用父类原逻辑
            return super().parse(path, title=title, meta=meta,
                                 on_progress=on_progress)
        from backend.rag.ingest.ocr.ocr_checkpoint import OcrCheckpoint
        ckpt = OcrCheckpoint(job_id)
        try:
            return self._parse_with_ckpt(path, title, meta,
                                          on_progress, ckpt)
        finally:
            ckpt.close()

    def _parse_with_ckpt(self, path, title, meta, on_progress, ckpt):
        import tempfile
        from pypdf import PdfReader
        total = len(PdfReader(path, strict=False).pages)
        limit = self._max_pages if self._max_pages > 0 else total
        limit = min(limit, total)

        # 读回已完成的页
        done = {int(p["page_no"]): p["text"] for p in ckpt.read_all()
                if p.get("text")}
        last = max(done.keys(), default=0)
        print(f"[resume-ocr] 已完成 {last}/{limit} 页，从 {last+1} 继续",
              flush=True)

        from backend.rag.ingest.ocr.gpu_coordinator import (
            acquire as _acq, release as _rel)
        _need = 1500 if os.environ.get("RAG_OCR_MODEL", "mobile") == "mobile" else 3500
        _acq("ocr", need_mb=_need)
        try:
            text_pages: List[ParsedPage] = []
            for pn, txt in sorted(done.items()):
                if txt.strip():
                    text_pages.append(ParsedPage(text=txt, page_no=pn))

            # 需要 OCR 的页
            need_ocr = [p for p in range(last + 1, limit + 1)]

            # 先做前 3 页探测（无文字 → 全部走 OCR）
            if last == 0:
                probe_ok = 0
                for i in range(min(3, limit)):
                    try:
                        t = (PdfReader(path, strict=False).pages[i]
                             .extract_text() or "").strip()
                        if len(t) >= DEFAULT_MIN_TEXT: probe_ok += 1
                    except Exception: pass
                if probe_ok == 0:
                    print(f"[resume-ocr] 扫描件，全部 OCR", flush=True)
                else:
                    # 混合：逐页抽文字
                    text_pages = []
                    need_ocr = []
                    for i in range(limit):
                        try:
                            t = (PdfReader(path, strict=False).pages[i]
                                 .extract_text() or "").strip()
                        except Exception: t = ""
                        if len(t) >= DEFAULT_MIN_TEXT:
                            text_pages.append(ParsedPage(text=t, page_no=i + 1))
                            ckpt.append_page(i + 1, t)
                        else:
                            need_ocr.append(i + 1)

            # 分批 OCR
            if need_ocr:
                self._ocr_pages_ckpt(path, need_ocr, limit,
                                      len(text_pages), on_progress, ckpt)
                # 从 checkpoint 读回所有 OCR 页
                for p in ckpt.read_all():
                    pn = int(p["page_no"])
                    if not any(tp.page_no == pn for tp in text_pages) and p.get("text"):
                        text_pages.append(ParsedPage(text=p["text"], page_no=pn))

            stat = os.stat(path)
            text_pages.sort(key=lambda p: p.page_no)
            return SourceDocument(
                path=os.path.abspath(path),
                source_type=SourceType.PDF,
                title=title or os.path.splitext(os.path.basename(path))[0],
                pages=tuple(text_pages), file_size=stat.st_size,
                meta={"ocr": True, "dpi": self._dpi,
                      "page_total": total, "pages_with_text": len(text_pages),
                      "resume_mode": True, **(meta or {})},
            )
        finally:
            _rel("ocr")

    def _ocr_pages_ckpt(self, path, page_nos, limit,
                         done_offset, on_progress, ckpt):
        from pdf2image import convert_from_path
        from backend.rag.ingest.ocr.tcm_corrections import correct as _corr
        import tempfile, os as _os

        tmp_dir = tempfile.mkdtemp(prefix="pdfresume_")
        processed = 0
        try:
            for start, end in self._group(page_nos, max_span=10):
                try:
                    imgs = convert_from_path(
                        path, dpi=self._dpi,
                        first_page=start, last_page=end)
                except Exception as e:
                    print(f"[resume-ocr] 渲染 {start}-{end} 失败: {e}",
                          flush=True)
                    continue
                paths = []
                try:
                    for img in imgs:
                        fd, tmp = tempfile.mkstemp(
                            suffix=".png", prefix="p_", dir=tmp_dir)
                        _os.close(fd); img.save(tmp, "PNG")
                        paths.append(tmp)
                    results = self._engine.recognize_batch(paths)
                    for pn, r in zip(range(start, end + 1), results):
                        txt = getattr(r, "text", "") or ""
                        try: txt = _corr(txt)
                        except Exception: pass
                        # 立刻落盘
                        ckpt.append_page(pn, txt)
                        processed += 1
                        if on_progress:
                            try: on_progress(done_offset + processed, limit)
                            except Exception: pass
                finally:
                    for p in paths:
                        try: _os.unlink(p)
                        except OSError: pass
                    for img in imgs:
                        try: img.close()
                        except Exception: pass
                    imgs.clear()
                    import gc as _gc; _gc.collect()
        finally:
            import shutil; shutil.rmtree(tmp_dir, ignore_errors=True)


def make_pdf_smart_parser_resume(*, lang: str = "ch", dpi: int = DEFAULT_DPI,
                                  max_pages: int = 0):
    from backend.rag.ingest.ocr.batch_engine import make_batch_engine
    eng = make_batch_engine(lang=lang)
    return PdfSmartParserResume(engine=eng, dpi=dpi, max_pages=max_pages)


__all__ = ["PdfSmartParserResume", "make_pdf_smart_parser_resume"]
