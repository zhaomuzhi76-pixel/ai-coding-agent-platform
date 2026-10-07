"""PDF 多模态管道：图文分层抽取 + caption + 双索引。

职责：
  1. 调 pdf_vision_parser 抽 {text, images}
  2. 调 image_captioner 生成 caption
  3. 组装带 images 字段的 chunk dict，返回给 MultimodalIndexer
  4. 图片单独入 image_index
不做：
  - 不做向量化（indexer 管）
  - 不做 HTTP（upload_router 管）
"""
from __future__ import annotations
import hashlib
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from backend.rag.ingest.pdf_vision_parser import parse_pdf_vision
from backend.rag.ingest import image_captioner

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_MULTIMODAL_PDF"
_IMG_DIR = "data/images"


def _is_scanned_pdf(pdf_path: str, sample: int = 3) -> bool:
    """探测前 N 页：每页 >=1 图 且 文本极少 → 扫描件。"""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        n = min(sample, len(doc))
        if n == 0:
            return False
        scanned = 0
        for i in range(n):
            page = doc[i]
            imgs = page.get_images()
            txt = (page.get_text() or "").strip()
            # 放宽：有图 + 文本 < 100 字（水印忽略）
            if len(imgs) >= 1 and len(txt) < 100:
                scanned += 1
        doc.close()
        return scanned == n
    except Exception:
        return False


def enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "0") == "1"


def _sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()[:16]


def _save_image(data: bytes, ext: str, kb: str, page_no: int,
                idx: int) -> str:
    """存原图到 data/images/<kb>/page_<n>_<idx>_<hash>.<ext>。返回相对路径。"""
    d = os.path.join(_IMG_DIR, kb)
    os.makedirs(d, exist_ok=True)
    h = _sha1(data)
    fn = f"page_{page_no:03d}_{idx:02d}_{h}.{ext}"
    full = os.path.join(d, fn)
    if not os.path.exists(full):
        with open(full, "wb") as f:
            f.write(data)
    return full


def process_pdf_multimodal(
        pdf_path: str, *,
        kb: str = "tcm",
        max_pages: int = 0,
        on_page: Optional[Callable[[int, int], None]] = None,
        cap_max: int = 3,     # 每页最多 caption 几张图
) -> List[Dict[str, Any]]:
    """核心入口。返回 chunk dict 列表（含 images），可直接喂 indexer.index_items。"""
    # [分支] 扫描件 → 渲染 + OCR；否则 → 图文分层抽取
    if _is_scanned_pdf(pdf_path):
        from backend.rag.ingest.pdf_scanned_parser import parse_pdf_scanned
        logger.info("[mm-pdf] 检测为扫描件，走 OCR 管道")
        pages = parse_pdf_scanned(pdf_path, max_pages=max_pages,
                                  on_page=on_page)
        _use_vlm = False       # 扫描件：用 OCR 文字作 caption，省 VLM
    else:
        pages = parse_pdf_vision(pdf_path, max_pages=max_pages)
        _use_vlm = True        # 图文分层：调 VLM 生成 caption
    total = len(pages)
    base = os.path.basename(pdf_path)
    out: List[Dict[str, Any]] = []
    img_total = 0

    for i, page in enumerate(pages):
        text = (page.text or "").strip()
        img_refs: List[Dict[str, Any]] = []
        for j, img in enumerate(page.images):
            path = _save_image(img.bytes, img.ext, kb, page.page_no, j)
            cap = ""
            if _use_vlm and image_captioner.enabled() and j < cap_max:
                cap = image_captioner.caption_png(img.bytes)
            elif not _use_vlm:
                # 扫描件：用该页 OCR 文字前 30 字作为 caption
                cap = (page.text or "").strip()[:30]
            img_id = f"img-{_sha1(img.bytes)}"
            img_refs.append({
                "id": img_id,
                "mime": f"image/{img.ext}",
                "source": "indexed",
                "url": "/" + path,          # 前端可直接访问
                "alt_text": cap,
                "page": page.page_no,
                "bbox": img.bbox,
            })
        img_total += len(img_refs)

        # 空页跳过
        if not text and not img_refs:
            if on_page:
                on_page(i + 1, total)
            continue

        chunk_id = f"{base}::p{page.page_no}"
        out.append({
            "chunk_id": chunk_id,
            "text": text or f"[图片页 p{page.page_no}]",
            "images": img_refs,
            "source": base,
            "source_path": pdf_path,
            "line_no": page.page_no,
            "role": "",
            "metadata": {"kb": kb, "page": page.page_no,
                          "n_images": len(img_refs)},
        })
        if on_page:
            on_page(i + 1, total)

    logger.info("[mm-pdf] %s: %d chunks, %d images",
                base, len(out), img_total)
    return out


__all__ = ["enabled", "process_pdf_multimodal"]
