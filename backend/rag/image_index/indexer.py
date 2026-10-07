"""图片向量索引编排。职责：
  图片/PDF页 → 原件落盘(origin_store) → CLIP 编码 → 入 image_index。
不做编码细节（clip_engine 管）、不做存储细节（store 管）、
不落原件细节（origin_store 管）。仅编排 + 报告。
支持 index_image / index_images / index_pdf。
image_id 规则：img-<origin_hash>（同内容幂等）。
"""
from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

DEFAULT_PDF_DPI = 150
DEFAULT_MAX_PAGES = 0     # 0 = 不限制

SUPPORTED_IMG_EXT = (
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff",
)


@dataclass(frozen=True)
class ImageIndexReport:
    total: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    image_ids: tuple = ()
    errors: tuple = ()
    elapsed_ms: int = 0
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not isinstance(self.image_ids, tuple):
            raise TypeError("image_ids must be tuple")
        if not isinstance(self.errors, tuple):
            raise TypeError("errors must be tuple")

    def to_dict(self) -> dict:
        return {
            "total": self.total, "indexed": self.indexed,
            "skipped": self.skipped, "failed": self.failed,
            "image_ids": list(self.image_ids),
            "errors": list(self.errors),
            "elapsed_ms": self.elapsed_ms,
            "meta": dict(self.meta),
        }


class ImageIndexer:
    def __init__(self, *, engine: Any, store: Any, origin_store: Any) -> None:
        if engine is None: raise ValueError("engine required")
        if store is None: raise ValueError("store required")
        if origin_store is None: raise ValueError("origin_store required")
        self._engine = engine
        self._store = store
        self._origin = origin_store

    # ---------- 单图 ----------
    def index_image(self, image_path: str, *, kb: str = "general",
                    text: str = "",
                    metadata: Optional[Mapping[str, Any]] = None) -> dict:
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in SUPPORTED_IMG_EXT:
            raise ValueError(f"不支持的图片扩展名: {ext}")
        if not os.path.isfile(image_path):
            raise FileNotFoundError(image_path)
        # 1) 原件落盘
        o = self._origin.put_file(image_path,
                                   original_name=os.path.basename(image_path))
        oh = o["hash"]
        # 2) CLIP 编码
        vec = self._engine.encode_image(image_path)
        # 3) 入 image_index
        iid = f"img-{oh}"
        w = h = 0
        try:
            from PIL import Image
            with Image.open(image_path) as im:
                w, h = im.size
        except Exception:  # silent-ok
            pass
        meta = {"kb": kb, **(metadata or {})}
        self._store.upsert(iid, vec, origin_hash=oh,
                            mime=f"image/{ext.lstrip('.')}",
                            width=w, height=h, text=text, metadata=meta)
        return {"image_id": iid, "origin_hash": oh, "dim": len(vec),
                "kb": kb, "path": image_path}

    # ---------- 批量 ----------
    def index_images(self, paths: Sequence[str], *, kb: str = "general"
                     ) -> ImageIndexReport:
        t0 = time.time()
        total = len(paths or ())
        ok = skipped = failed = 0
        ids: list = []
        errs: list = []
        for p in paths or ():
            if not p or not os.path.isfile(p):
                skipped += 1; continue
            try:
                r = self.index_image(p, kb=kb)
                ids.append(r["image_id"]); ok += 1
            except Exception as e:
                failed += 1
                errs.append(f"{p}: {type(e).__name__}: {e}")
        return ImageIndexReport(
            total=total, indexed=ok, skipped=skipped, failed=failed,
            image_ids=tuple(ids), errors=tuple(errs),
            elapsed_ms=int((time.time() - t0) * 1000),
            meta={"kb": kb})

    # ---------- PDF 每页转图 ----------
    def index_pdf(self, pdf_path: str, *, kb: str = "general",
                  dpi: int = DEFAULT_PDF_DPI,
                  max_pages: int = DEFAULT_MAX_PAGES
                  ) -> ImageIndexReport:
        if dpi <= 0: raise ValueError("dpi must be > 0")
        if max_pages < 0: raise ValueError("max_pages must be >= 0")
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(pdf_path)
        try:
            from pdf2image import convert_from_path
        except ImportError as e:
            raise RuntimeError("未安装 pdf2image") from e

        t0 = time.time()
        total_known = self._count_pages(pdf_path)
        limit = max_pages if max_pages > 0 else total_known
        limit = min(limit, total_known)

        ok = failed = 0
        ids: list = []
        errs: list = []
        for page_no in range(1, limit + 1):
            try:
                imgs = convert_from_path(pdf_path, dpi=dpi,
                                          first_page=page_no,
                                          last_page=page_no)
                if not imgs:
                    continue
                r = self._index_pil(imgs[0], pdf_path, page_no, kb)
                ids.append(r["image_id"]); ok += 1
            except Exception as e:
                failed += 1
                errs.append(f"page {page_no}: {type(e).__name__}: {e}")
        return ImageIndexReport(
            total=limit, indexed=ok, skipped=0, failed=failed,
            image_ids=tuple(ids), errors=tuple(errs),
            elapsed_ms=int((time.time() - t0) * 1000),
            meta={"kb": kb, "source_pdf": os.path.basename(pdf_path),
                  "dpi": dpi})

    # ---------- 内部 ----------
    def _index_pil(self, pil_img: Any, pdf_path: str,
                   page_no: int, kb: str) -> dict:
        """PIL 图 → 临时 PNG → 原件保存 + CLIP 编码 + upsert → 删临时。"""
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix=".png", prefix="imgidx_")
        os.close(fd)
        try:
            pil_img.save(tmp, format="PNG")
            o = self._origin.put_file(
                tmp, original_name=f"{os.path.basename(pdf_path)}#p{page_no}.png")
            oh = o["hash"]
            vec = self._engine.encode_image(tmp)
            iid = f"img-{oh}"
            w, h = getattr(pil_img, "size", (0, 0))
            meta = {"kb": kb, "source_pdf": os.path.basename(pdf_path),
                    "page_no": page_no}
            self._store.upsert(iid, vec, origin_hash=oh, mime="image/png",
                                width=int(w), height=int(h),
                                text=f"{os.path.basename(pdf_path)} 第{page_no}页",
                                metadata=meta)
            return {"image_id": iid, "origin_hash": oh,
                    "page_no": page_no}
        finally:
            try: os.unlink(tmp)
            except OSError: pass

    @staticmethod
    def _count_pages(pdf_path: str) -> int:
        try:
            from pypdf import PdfReader
            return len(PdfReader(pdf_path).pages)
        except Exception:
            return 0


def make_image_indexer(*, engine: Any, store: Any,
                       origin_store: Any) -> ImageIndexer:
    return ImageIndexer(engine=engine, store=store, origin_store=origin_store)


__all__ = ["ImageIndexer", "ImageIndexReport",
           "make_image_indexer",
           "DEFAULT_PDF_DPI", "DEFAULT_MAX_PAGES", "SUPPORTED_IMG_EXT"]
