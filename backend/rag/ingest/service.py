"""RAG 采集编排。职责：文件 → 解析 → 切块 → 索引（复用 L13.0/L13.1 + L7）。
不实现解析（parsers 管）、不切片（chunker 管）、不 upsert（indexer 管）。
仅负责"把一条条文件走通全流程并汇总报告"。
不落盘除向量库外的任何东西。不调 LLM。"""
from __future__ import annotations
import os
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

from backend.rag.ingest.contracts import (
    IngestReport, SourceDocument)
from backend.rag.ingest.parsers import (
    ParserDispatcher, get_default_dispatcher)

DEFAULT_BATCH = 64
DEFAULT_KB = "general"
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB（与 upload 层对齐）

@dataclass(frozen=True)
class IngestOptions:
    """采集选项。kb 打入 metadata 用于多库隔离。"""
    kb: str = DEFAULT_KB
    source: str = ""              # 覆盖 source 字段（默认用文件名）
    batch_size: int = DEFAULT_BATCH
    dry_run: bool = False         # 只解析不索引
    skip_empty: bool = True       # 空文档不计入 failed
    max_file_size: int = MAX_FILE_SIZE
    on_progress: Any = None       # Callable[[int, int], None] | None
    extra_meta: Any = None        # [NEW] 附加 metadata（dict），合并到每个 chunk

    def __post_init__(self) -> None:
        if not self.kb.strip():
            raise ValueError("IngestOptions.kb required")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if self.max_file_size <= 0:
            raise ValueError("max_file_size must be > 0")
        if self.extra_meta is not None and not isinstance(self.extra_meta, dict):
            raise ValueError("extra_meta must be dict or None")

class IngestService:
    """把"文件路径 → 索引"编排成一步。
    chunker / indexer 由外部注入（装配层管）。
    dispatcher 缺省用全局默认。"""
    def __init__(self, *, chunker: Any, indexer: Any,
                 dispatcher: Optional[ParserDispatcher] = None) -> None:
        if chunker is None:
            raise ValueError("chunker required")
        if indexer is None:
            raise ValueError("indexer required")
        self._chunker = chunker
        self._indexer = indexer
        self._dispatcher = dispatcher or get_default_dispatcher()

    def ingest_paths(self, paths: Sequence[str], *,
                     options: Optional[IngestOptions] = None) -> IngestReport:
        opt = options or IngestOptions()
        t0 = time.time()
        total = len(paths)
        ok = 0
        failed = 0
        chunks_total = 0
        errs: list[str] = []

        for p in paths:
            try:
                n = self._ingest_one(p, opt)
                chunks_total += n
                ok += 1
            except _SkipFile as e:
                if not opt.skip_empty:
                    failed += 1
                    errs.append(f"{p}: {e}")
                else:
                    ok += 1
            except Exception as e:
                failed += 1
                errs.append(f"{p}: {type(e).__name__}: {e}")

        return IngestReport(
            total=total, succeeded=ok, failed=failed,
            chunks_indexed=chunks_total, errors=tuple(errs),
            elapsed_ms=int((time.time() - t0) * 1000),
            meta={"kb": opt.kb, "dry_run": opt.dry_run},
        )

    def ingest_dir(self, directory: str, *,
                   options: Optional[IngestOptions] = None,
                   extensions: Optional[Iterable[str]] = None,
                   recursive: bool = True) -> IngestReport:
        root = os.path.expanduser(directory)
        if not os.path.isdir(root):
            raise NotADirectoryError(root)
        exts = {e.lower() for e in (extensions or
                (".pdf", ".md", ".markdown", ".txt"))}
        paths: list[str] = []
        if recursive:
            for base, _, files in os.walk(root):
                for fn in files:
                    if os.path.splitext(fn)[1].lower() in exts:
                        paths.append(os.path.join(base, fn))
        else:
            for fn in os.listdir(root):
                full = os.path.join(root, fn)
                if os.path.isfile(full) and \
                        os.path.splitext(fn)[1].lower() in exts:
                    paths.append(full)
        paths.sort()
        return self.ingest_paths(paths, options=options)

    def parse_chunks(self, path: str, *,
                     options: Optional[IngestOptions] = None) -> list:
        """只解析 + 分块，不索引。返回 MultimodalChunk 列表供审核。
        与 ingest_paths 边界：只走到 chunker，不调 indexer。"""
        import os as _os
        opt = options or IngestOptions()
        self._check_size(path, opt)
        # [MM-PDF] 多模态 PDF 分支（env 开关，默认关闭）
        if path.lower().endswith(".pdf"):
            try:
                from backend.rag.ingest import pdf_multimodal_pipeline as _mm
                if _mm.enabled():
                    return self._parse_pdf_multimodal(path, opt)
            except Exception as _e:
                import logging as _log
                _log.getLogger(__name__).warning(
                    "[mm-pdf] fallback to text: %r", _e)
        doc = self._dispatcher.parse(path, on_progress=opt.on_progress,
                                     meta=opt.extra_meta)
        if not doc.pages:
            return []
        source = opt.source or _os.path.basename(doc.path)
        origin_hash = ""
        if "|origin:" in source:
            source, _, tail = source.partition("|origin:")
            origin_hash = tail.strip()
        chunks: list = []
        for page in doc.pages:
            metadata: dict = {"kb": opt.kb, "page_no": page.page_no,
                              "doc_title": doc.title,
                              "doc_path": doc.path,
                              "doc_hash": doc.file_hash}
            if opt.extra_meta:
                metadata.update(opt.extra_meta)
            if origin_hash:
                metadata["origin_hash"] = origin_hash
            if page.section:
                metadata["section"] = page.section
            cs = self._chunker.chunk_text(
                text=page.text, source=source,
                source_path=doc.path, line_no=page.page_no,
                images=page.images or None, metadata=metadata)
            chunks.extend(cs)
        return chunks

    def _parse_pdf_multimodal(self, path: str, opt) -> list:
        """[MM-PDF] 图文分层抽取 + OCR/caption + 组装 chunk。"""
        import os as _os
        from backend.rag.ingest import pdf_multimodal_pipeline as _mm
        items = _mm.process_pdf_multimodal(
            path, kb=opt.kb,
            on_page=opt.on_progress,
            max_pages=0,
            cap_max=3,
        )
        if not items:
            return []
        return self._chunker.chunk_items(items)


    def preview(self, path: str, *, options: Optional[IngestOptions] = None
                ) -> SourceDocument:
        """只解析不索引。用于前端预览/校验。"""
        opt = options or IngestOptions(dry_run=True)
        self._check_size(path, opt)
        return self._dispatcher.parse(path)

    # ---------- 内部 ----------
    def _ingest_one(self, path: str, opt: IngestOptions) -> int:
        self._check_size(path, opt)
        doc = self._dispatcher.parse(path, on_progress=opt.on_progress,
                                     meta=opt.extra_meta)
        if not doc.pages:
            raise _SkipFile("no text content")
        source = opt.source or os.path.basename(doc.path)
        # source 里 "|origin:xxx" → metadata.origin_hash
        origin_hash = ""
        if "|origin:" in source:
            source, _, tail = source.partition("|origin:")
            origin_hash = tail.strip()
        chunks = []
        for page in doc.pages:
            metadata = {"kb": opt.kb, "page_no": page.page_no,
                        "doc_title": doc.title,
                        "doc_path": doc.path,
                        "doc_hash": doc.file_hash}
            if opt.extra_meta:
                metadata.update(opt.extra_meta)
            if origin_hash:
                metadata["origin_hash"] = origin_hash
            if page.section:
                metadata["section"] = page.section
            cs = self._chunker.chunk_text(
                text=page.text, source=source,
                source_path=doc.path, line_no=page.page_no,
                images=page.images or None, metadata=metadata)
            chunks.extend(cs)
        if opt.dry_run:
            return len(chunks)
        rep = self._indexer.index_chunks(chunks, batch_size=opt.batch_size)
        if rep.errors:
            raise RuntimeError(f"index errors: {rep.errors[:2]}")
        return rep.indexed

    @staticmethod
    def _check_size(path: str, opt: IngestOptions) -> None:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        sz = os.path.getsize(path)
        if sz > opt.max_file_size:
            raise ValueError(
                f"file too large ({sz} > {opt.max_file_size})")

class _SkipFile(Exception):
    """空文件/无内容 — 可选的跳过而非失败。"""

def make_ingest_service(*, chunker: Any, indexer: Any,
                        dispatcher: Optional[ParserDispatcher] = None
                        ) -> IngestService:
    return IngestService(chunker=chunker, indexer=indexer,
                        dispatcher=dispatcher)

__all__ = ["IngestService", "IngestOptions", "make_ingest_service",
           "DEFAULT_BATCH", "DEFAULT_KB", "MAX_FILE_SIZE"]
