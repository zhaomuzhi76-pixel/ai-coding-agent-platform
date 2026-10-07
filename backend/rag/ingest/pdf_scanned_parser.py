"""扫描件 PDF 解析：渲染整页 + OCR → 图文一体化。

职责：
  - 输入扫描件 PDF → 输出 [PageTextImage]
  - 每页：渲染 PNG（dpi 180）→ PaddleOCR 识别 → 组装
不做：
  - 不做向量化、不做 caption（pipeline 管）
  - 不区分正文/插图（扫描件版式多变，统一按"整页"处理）

工业级：
  - 引擎复用 engine_pool（不重复加载）
  - 临时 PNG 用后即删
  - 单页异常不中断
"""
from __future__ import annotations
import logging
import os
import tempfile
from typing import Any, List, Optional

from backend.rag.ingest.pdf_vision_parser import PageImage, PageTextImage

logger = logging.getLogger(__name__)

_DEFAULT_DPI = 120
_LANG = "chinese_cht"   # 本草纲目用繁体


def _get_engine():
    """复用全局 OCR 引擎池。"""
    try:
        from backend.rag.ingest.ocr.engine_pool import get_default_pool
        return get_default_pool().get(_LANG)
    except Exception as e:
        logger.warning("[scanned] 引擎池不可用: %r，回退 ch", e)
        from backend.rag.ingest.ocr.engine_pool import get_default_pool
        return get_default_pool().get("ch")


def _ocr_png_bytes(engine: Any, png_bytes: bytes) -> str:
    """写临时 PNG → 调 OCR → 删临时。返回拼接文本。"""
    fd, tmp = tempfile.mkstemp(suffix=".png", prefix="scan_")
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            f.write(png_bytes)
        result = engine.recognize(tmp)
        lines = getattr(result, "lines", ()) or ()
        return "\n".join(
            (getattr(ln, "text", "") or "").strip()
            for ln in lines
            if getattr(ln, "text", ""))
    except Exception as e:
        logger.warning("[scanned] OCR 失败: %r", e)
        return ""
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def parse_pdf_scanned(pdf_path: str, *,
                      max_pages: int = 0,
                      dpi: int = _DEFAULT_DPI,
                      on_page: Optional[Any] = None
                      ) -> List[PageTextImage]:
    """主入口：扫描 PDF → [PageTextImage]（text=OCR，images=(整页图,)）。"""
    if not pdf_path or not os.path.isfile(pdf_path):
        raise FileNotFoundError(pdf_path)

    try:
        import fitz
    except ImportError as e:
        raise RuntimeError("PyMuPDF 未安装") from e

    engine = _get_engine()
    doc = fitz.open(pdf_path)
    total = len(doc)
    limit = total if max_pages <= 0 else min(max_pages, total)

    out: List[PageTextImage] = []
    for i in range(limit):
        page_no = i + 1
        try:
            page = doc[i]
            # 1) 渲染整页
            pix = page.get_pixmap(dpi=dpi)
            png_bytes = pix.tobytes("png")
            # 2) OCR
            text = _ocr_png_bytes(engine, png_bytes)
            # 3) 组装：整页图作为该页的 image
            img = PageImage(bytes=png_bytes, ext="png",
                            width=pix.width, height=pix.height)
            out.append(PageTextImage(
                page_no=page_no, text=text, images=(img,),
                meta={"scanned": True, "chars": len(text),
                      "img_w": pix.width, "img_h": pix.height}))
        except Exception as e:
            logger.warning("[scanned] page %d 失败: %r", page_no, e)
            out.append(PageTextImage(page_no=page_no, text="",
                                     images=(), meta={"error": str(e)}))
        if on_page:
            try:
                on_page(page_no, limit)
            except Exception:
                pass

    doc.close()
    logger.info("[scanned] %s: %d/%d 页",
                os.path.basename(pdf_path), len(out), total)
    return out


__all__ = ["parse_pdf_scanned"]
