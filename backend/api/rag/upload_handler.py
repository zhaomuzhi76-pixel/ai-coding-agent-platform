"""RAG 文件上传 handler。职责：接收 multipart 上传 → 临时文件 → 调 ingest → 清理。
不落盘持久化（仅用系统 tempdir）、不实现解析/索引、不持状态。
单文件大小/类型限制；临时文件用 finally 保证删除。
支持 lang 参数（临时替换 dispatcher 的 OCR 语言）。
"""
from __future__ import annotations
import os
import tempfile
from typing import Any, Optional

MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1GB（与 upload_router 对齐）
# 已废弃：路由走 upload_router.py → worker → service
ALLOWED_EXT = {
    ".pdf", ".md", ".markdown", ".txt", ".log",
    ".jpg", ".jpeg", ".png", ".bmp", ".webp",
    ".tif", ".tiff",
    ".docx", ".xlsx", ".pptx", ".html", ".htm",
}

# UI 支持的语言白名单
SUPPORTED_OCR_LANGS = ("", "ch", "chinese_cht", "en", "japan", "korean")


def _check_ext(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(
            f"不支持的扩展名 {ext!r}，仅支持 {sorted(ALLOWED_EXT)}")
    return ext


def _check_size(content: bytes) -> None:
    n = len(content)
    if n == 0:
        raise ValueError("empty file")
    if n > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"file too large ({n} > {MAX_UPLOAD_BYTES})")


def _make_dispatcher_for_lang(lang: str) -> Any:
    """为指定语言构建 dispatcher（走 engine_pool 单例，不重复加载模型）。"""
    from backend.rag.ingest.ocr.engine_pool import get_default_pool
    from backend.rag.ingest.parsers.dispatcher import ParserDispatcher
    from backend.rag.ingest.parsers.pdf_ocr_parser import PdfOcrParser
    from backend.rag.ingest.parsers.image_parser import ImageParser
    from backend.rag.ingest.parsers.pdf_parser import PdfParser
    from backend.rag.ingest.parsers.markdown_parser import MarkdownParser
    from backend.rag.ingest.parsers.text_parser import TextParser

    pool = get_default_pool()
    eng = pool.get(lang)
    from backend.rag.ingest.parsers.docx_parser import DocxParser
    from backend.rag.ingest.parsers.xlsx_parser import XlsxParser
    from backend.rag.ingest.parsers.pptx_parser import PptxParser
    from backend.rag.ingest.parsers.html_parser import HtmlParser
    return ParserDispatcher(
        parsers=(PdfParser(), ImageParser(engine=eng),
                 MarkdownParser(), TextParser(),
                 DocxParser(), XlsxParser(), PptxParser(), HtmlParser()),
        auto_ocr=True, lang=lang, pool=pool,
        pdf_ocr_parser=PdfOcrParser(engine=eng),
    )


def _ingest_with_lang(service: Any, tmp_path: str,
                      opt: Any, lang: str,
                      origin_hash: str = "") -> Any:
    """若指定非默认语言，临时替换 service 的 dispatcher。
    origin_hash 通过 IngestOptions 的 source 字段注入 metadata。"""
    if origin_hash:
        opt = _with_origin(opt, origin_hash)
    if not lang or lang == "ch":
        return service.ingest_paths([tmp_path], options=opt)
    saved = getattr(service, "_dispatcher", None)
    try:
        service._dispatcher = _make_dispatcher_for_lang(lang)  # noqa: SLF001
        return service.ingest_paths([tmp_path], options=opt)
    finally:
        if saved is not None:
            service._dispatcher = saved  # noqa: SLF001


def _with_origin(opt: Any, origin_hash: str) -> Any:
    """把 origin_hash 打进去 —— 复用 IngestOptions.source 承载。"""
    from backend.rag.ingest.service import IngestOptions
    src = (opt.source or "") + f"|origin:{origin_hash}"
    return IngestOptions(
        kb=opt.kb, source=src, batch_size=opt.batch_size,
        dry_run=opt.dry_run, skip_empty=opt.skip_empty,
        max_file_size=opt.max_file_size)


def upload_bytes_handler(service: Any, *, filename: str,
                         content: bytes, kb: str = "general",
                         batch_size: int = 64,
                         dry_run: bool = False,
                         lang: str = "") -> dict:
    """核心：bytes → 临时文件 → ingest → 清理。"""
    ext = _check_ext(filename)
    _check_size(content)
    if lang not in SUPPORTED_OCR_LANGS:
        raise ValueError(
            f"不支持的 lang {lang!r}，支持: {SUPPORTED_OCR_LANGS}")

    from backend.rag.ingest.service import IngestOptions
    opt = IngestOptions(
        kb=(kb or "general").strip() or "general",
        source=os.path.basename(filename),
        batch_size=int(batch_size),
        dry_run=bool(dry_run),
    )
    # 1) 保存原件
    origin = _save_origin(content, filename=filename, ext=ext)
    origin_hash = origin.get("hash", "")

    fd, tmp_path = tempfile.mkstemp(suffix=ext, prefix="ragup_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        rep = _ingest_with_lang(service, tmp_path, opt, lang,
                                 origin_hash=origin_hash)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    out = rep.to_dict()
    out["filename"] = os.path.basename(filename)
    out["kb"] = opt.kb
    if lang:
        out["lang"] = lang
    out["origin"] = {"hash": origin_hash,
                     "size": origin.get("size", 0),
                     "ext": origin.get("ext", "")}
    return out


__all__ = ["MAX_UPLOAD_BYTES", "ALLOWED_EXT", "SUPPORTED_OCR_LANGS",
           "upload_bytes_handler"]

def _save_origin(content: bytes, *, filename: str,
                 ext: str) -> dict:
    """上传时保存原件到持久化目录。失败不阻塞索引。"""
    try:
        from backend.storage.origin_store import get_default_origin_store
        store = get_default_origin_store()
        return store.put_bytes(content, ext=ext.lstrip("."),
                                original_name=filename)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
