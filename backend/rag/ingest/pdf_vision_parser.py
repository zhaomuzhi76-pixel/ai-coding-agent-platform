"""PDF 视觉解析器：图文分层抽取（PyMuPDF）。

职责：
  - 输入 PDF 路径 → 输出 [PageTextImage]
  - 每页：抽文本 + 抽内嵌图片 + 计算 bbox
不做：
  - 不做 OCR（那是 pdf_ocr_parser 的职责）
  - 不做 caption（那是 image_captioner 的职责）
  - 不做向量化（那是 indexer 的职责）

工业级：
  - 单页异常不中断（logger.warning 后继续）
  - max_pages=0 表示不限制
  - 大图过滤（>20KB）+ 小图过滤（<50x50）
"""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

_MIN_IMG_BYTES = 1024           # 忽略 < 1KB 的图标
_MIN_IMG_SIDE = 50              # 忽略 < 50px 的贴图
_MAX_PAGES_DEFAULT = 0          # 0 = 全部


@dataclass(frozen=True)
class PageImage:
    """单张内嵌图。"""
    bytes: bytes
    ext: str                    # 'png' / 'jpeg' / ...
    width: int = 0
    height: int = 0
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)


@dataclass(frozen=True)
class PageTextImage:
    """单页的图文输出。"""
    page_no: int
    text: str = ""
    images: Tuple[PageImage, ...] = ()
    meta: dict = field(default_factory=dict)


def _is_useful(img: PageImage) -> bool:
    """过滤装饰性小图。"""
    if len(img.bytes) < _MIN_IMG_BYTES:
        return False
    if img.width and img.height:
        if img.width < _MIN_IMG_SIDE or img.height < _MIN_IMG_SIDE:
            return False
    return True


def _extract_images(page: Any) -> List[PageImage]:
    """从 fitz.Page 抽所有内嵌图。"""
    out: List[PageImage] = []
    try:
        img_list = page.get_images(full=True)
    except Exception as e:
        logger.debug("[vision] get_images failed: %r", e)
        return out

    for img_info in img_list:
        try:
            xref = img_info[0]
            base = page.parent.extract_image(xref)
            if not base:
                continue
            raw = base.get("image") or b""
            ext = str(base.get("ext") or "png").lower()
            w = int(base.get("width") or 0)
            h = int(base.get("height") or 0)

            # bbox：该 xref 在本页的所有位置，取第一个
            bbox = (0.0, 0.0, 0.0, 0.0)
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    r = rects[0]
                    bbox = (float(r.x0), float(r.y0), float(r.x1), float(r.y1))
            except Exception:
                pass

            pi = PageImage(bytes=raw, ext=ext, width=w, height=h, bbox=bbox)
            if _is_useful(pi):
                out.append(pi)
        except Exception as e:
            logger.debug("[vision] img xref=%r failed: %r",
                         img_info[0] if img_info else "?", e)
            continue
    return out


def _page_text(page: Any) -> str:
    """按阅读顺序抽文本。"""
    try:
        t = page.get_text("text") or ""
        return t.strip()
    except Exception as e:
        logger.debug("[vision] get_text failed: %r", e)
        return ""


def parse_pdf_vision(pdf_path: str, *,
                     max_pages: int = _MAX_PAGES_DEFAULT,
                     on_page: Optional[Any] = None) -> List[PageTextImage]:
    """主入口：PDF → [PageTextImage]。单页异常不中断。

    Args:
        pdf_path: PDF 路径
        max_pages: 最多解析页数（0 = 全部）
        on_page: 可选回调 on_page(cur, total)
    """
    if not pdf_path or not os.path.isfile(pdf_path):
        raise FileNotFoundError(pdf_path)

    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError("PyMuPDF 未安装：pip install PyMuPDF") from e

    doc = fitz.open(pdf_path)
    total = len(doc)
    limit = total if max_pages <= 0 else min(max_pages, total)

    out: List[PageTextImage] = []
    for i in range(limit):
        page_no = i + 1
        try:
            page = doc[i]
            text = _page_text(page)
            imgs = _extract_images(page)
            out.append(PageTextImage(
                page_no=page_no, text=text,
                images=tuple(imgs),
                meta={"n_images": len(imgs), "chars": len(text)}))
        except Exception as e:
            logger.warning("[vision] page %d failed: %r", page_no, e)
            out.append(PageTextImage(page_no=page_no, text="",
                                     images=(), meta={"error": str(e)}))
        if on_page:
            try:
                on_page(page_no, limit)
            except Exception:
                pass

    doc.close()
    logger.info("[vision] %s: %d/%d pages parsed",
                os.path.basename(pdf_path), len(out), total)
    return out


__all__ = ["PageImage", "PageTextImage", "parse_pdf_vision"]
