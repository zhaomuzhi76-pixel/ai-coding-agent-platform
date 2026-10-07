"""PDF OCR 批量解析器（V9.3 完整版）。
职责：PDF → 多页批量 OCR → SourceDocument。
优化点：
  A 批量：一次送 N 页给引擎
  B 并发：引擎内部批量推理
  C 空白页：像素范围检测，空白页跳过 OCR
  D 分批流水：每批完成立刻 on_progress
  E 内存守护：RSS>2GB 时 GC+暂停；>3GB 自动降级 batch
"""
from __future__ import annotations
import os
import shutil
import tempfile
from typing import Any, List, Optional, Tuple

from backend.rag.ingest.contracts import (

    ParsedPage, SourceDocument, SourceType)
from backend.rag.ingest.parsers.pdf_ocr_parser import (
    DEFAULT_DPI, MIN_PAGE_CHARS)

from backend.rag.ingest.parsers.batch_memory import (
    BLANK_RANGE, DEFAULT_BATCH, RSS_WARN_MB, RSS_DANGER_MB,
    read_rss_mb as _read_rss_mb, release_imgs as _release_imgs,
)





class PdfOcrParserBatch:
    def __init__(self, *, engine: Any = None, dpi: int = DEFAULT_DPI,
                 batch_size: int = DEFAULT_BATCH, max_pages: int = 0) -> None:
        if dpi <= 0: raise ValueError("dpi must be > 0")
        if batch_size <= 0: raise ValueError("batch_size must be > 0")
        if max_pages < 0: raise ValueError("max_pages must be >= 0")
        if engine is None:
            from backend.rag.ingest.ocr.batch_engine import make_batch_engine
            engine = make_batch_engine(lang="ch")
        self._engine = engine
        self._dpi = dpi
        self._batch = batch_size
        self._max_pages = max_pages

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".pdf")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None,
              on_progress=None,
              start_page: int = 0) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        total = self._count_pages(path)
        limit = self._max_pages if self._max_pages > 0 else total
        limit = min(limit, total)

        # [GPU-AUTO] 请求独占 GPU（自动释放其他组件）
        from backend.rag.ingest.ocr.gpu_coordinator import (
            acquire as _gpu_acq, release as _gpu_rel)
        _need = 1500 if os.environ.get("RAG_OCR_MODEL", "mobile") == "mobile" else 3500
        _gpu_ok = _gpu_acq("ocr", need_mb=_need)
        import logging as _lg
        _lg.getLogger(__name__).info(
            "[pdf-ocr] GPU 获取: %s", "✅ 成功" if _gpu_ok else "❌ 降级 CPU")

        tmp_dir = tempfile.mkdtemp(prefix="pdfocr_batch_")
        pages: List[ParsedPage] = []
        # [RESUME] 断点续传：按 PDF 内容哈希读 checkpoint
        from backend.rag.ingest.ocr import ocr_checkpoint as _ck
        try:
            _last = _ck.get_last_page(path)
        except Exception:
            _last = 0
        _first_base = max(int(start_page or 0), int(_last or 0))
        first = max(1, min(_first_base + 1, limit + 1))
        if first > 1:
            print(f'[resume] OCR 从第 {first} 页继续 (已处理 {first-1}/{limit})', flush=True)
        done = first - 1
        try:
            for start in range(first, limit + 1, self._batch):
                # [MEM_GUARD] 每批前检查内存
                _rss = _read_rss_mb()
                if _rss > RSS_WARN_MB:
                    import gc as _gc, time as _t
                    _gc.collect(); _t.sleep(0.5)
                    if _read_rss_mb() > RSS_DANGER_MB:
                        print(f"[MEM_GUARD] RSS={_rss:.0f}MB 过高，本批减半", flush=True)
                        self._batch = max(1, self._batch // 2)

                end = min(start + self._batch - 1, limit)
                imgs = self._render_pages(path, start, end)

                # C：空白页过滤
                keep: List[Tuple[int, Any]] = []
                for off, img in enumerate(imgs):
                    page_no = start + off
                    if self._is_blank(img):
                        done += 1

                        # [PER_PAGE_CKPT] 每页立即写盘（防 kill -9 丢 checkpoint）

                        try: _ck.advance(path, done, total=limit)

                        except Exception: pass

                        if on_progress:
                            try: on_progress(done, limit)
                            except Exception: pass
                        continue
                    keep.append((page_no, img))
                if not keep:
                    _release_imgs(imgs)
                    try:
                        _ck.advance(path, done, total=limit)
                    except Exception:
                        pass
                    continue

                tmp_paths: List[str] = []
                page_nos: List[int] = []
                try:
                    for page_no, img in keep:
                        fd, tmp = tempfile.mkstemp(
                            suffix=".png", prefix="p_", dir=tmp_dir)
                        os.close(fd)
                        img.save(tmp, format="PNG")
                        tmp_paths.append(tmp); page_nos.append(page_no)

                    results = self._engine.recognize_batch(tmp_paths)
                    for page_no, res in zip(page_nos, results):
                        text = getattr(res, "text", "") or ""
                        # [C] 中医术语纠错
                        try:
                            from backend.rag.ingest.ocr.tcm_corrections import (
                                correct as _corr)
                            text = _corr(text)
                        except Exception:
                            pass
                        done += 1
                        if on_progress:
                            try: on_progress(done, limit)
                            except Exception: pass
                        if len(text.strip()) >= MIN_PAGE_CHARS:
                            pages.append(ParsedPage(text=text, page_no=page_no))
                finally:
                    for t in tmp_paths:
                        try: os.unlink(t)
                        except OSError: pass
                    _release_imgs(imgs)
        finally:
            try:
                _ck.advance(path, done, total=limit)
            except Exception:
                pass
            shutil.rmtree(tmp_dir, ignore_errors=True)
            import gc as _gc
            _gc.collect()
            # [GPU-AUTO] 用完立即释放（给对话/编程大模型让位）
            try:
                _gpu_rel("ocr")
                _lg.getLogger(__name__).info(
                    "[pdf-ocr] GPU 已释放（空闲 %sMB）",
                    __import__("backend.rag.ingest.ocr.gpu_coordinator",
                               fromlist=["free_mb"]).free_mb())
            except Exception as _e:
                _lg.getLogger(__name__).warning(
                    "[pdf-ocr] GPU 释放失败: %r", _e)

        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path),
            source_type=SourceType.PDF,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages),
            file_size=stat.st_size,
            meta={"ocr": True, "dpi": self._dpi, "page_total": total,
                  "pages_with_text": len(pages), "batch_mode": True,
                  "batch_size": self._batch, **(meta or {})},
        )


    @staticmethod
    def _count_pages(path: str) -> int:
        """[ROBUST] 多层 fallback 算页数，兼容大/加密/畸形 PDF。"""
        # 尝试 1: pypdf 宽松模式
        try:
            from pypdf import PdfReader
            reader = PdfReader(path, strict=False)
            if reader is not None and hasattr(reader, "pages"):
                return len(reader.pages)
        except Exception as e:
            print(f"[count_pages] pypdf 失败: {type(e).__name__}: {e}",
                  flush=True)

        # 尝试 2: pikepdf（更强）
        try:
            import pikepdf
            with pikepdf.open(path) as pdf:
                return len(pdf.pages)
        except Exception:
            pass

        # 尝试 3: pdfinfo 命令行
        try:
            import subprocess, re
            out = subprocess.check_output(
                ["pdfinfo", path], stderr=subprocess.DEVNULL,
                timeout=30, text=True)
            m = re.search(r"Pages:\s+(\d+)", out)
            if m:
                return int(m.group(1))
        except Exception:
            pass

        # 尝试 4: pdf2image 渲染（用异常探查）
        try:
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(path)
            return int(info.get("Pages", 0))
        except Exception as e:
            raise RuntimeError(
                f"无法读取 PDF 页数（pypdf/pikepdf/pdfinfo/pdf2image 全失败）: {e}"
            ) from e

    def _render_pages(self, path: str, start: int, end: int) -> List[Any]:
        from pdf2image import convert_from_path
        return convert_from_path(path, dpi=self._dpi,
                                 first_page=start, last_page=end)

    @staticmethod
    def _is_blank(img: Any) -> bool:
        try:
            lo, hi = img.convert("L").getextrema()
            return (hi - lo) < BLANK_RANGE
        except Exception:
            return False




def make_pdf_ocr_parser_batch(*, lang: str = "ch", dpi: int = DEFAULT_DPI,
                              use_gpu: bool = False, max_pages: int = 0,
                              batch_size: int = DEFAULT_BATCH):
    from backend.rag.ingest.ocr.batch_engine import make_batch_engine
    eng = make_batch_engine(lang=lang, use_gpu=use_gpu)
    return PdfOcrParserBatch(engine=eng, dpi=dpi,
                             batch_size=batch_size, max_pages=max_pages)


__all__ = ["PdfOcrParserBatch", "make_pdf_ocr_parser_batch",
           "BLANK_RANGE", "DEFAULT_BATCH", "RSS_WARN_MB", "RSS_DANGER_MB"]

def _release_gpu_memory() -> None:
    """[GPU_RELEASE] 主动释放 Paddle/CUDA 显存。任务结束后必调。"""
    try:
        import paddle
        if paddle.is_compiled_with_cuda():
            paddle.device.cuda.empty_cache()
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    try:
        import gc
        gc.collect()
    except Exception:
        pass

