"""异步采集 worker。职责：后台线程执行 ingest，实时更新进度。
不解析（service 管）、不调度（pool 管）、不持久化（registry 管）。
通过 ThreadPoolExecutor 并发；支持取消（粗粒度：检查标志）。
临时文件由本 worker 负责清理（cleanup=True，默认）。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

# [ASYNC_OCR] 专用线程池：OCR 在线程里跑，不阻塞事件循环
from concurrent.futures import ThreadPoolExecutor as _Tpe
_OCR_EXECUTOR = _Tpe(max_workers=2, thread_name_prefix="ocr-")


import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from backend.rag.ingest.jobs.contracts import (
    IngestJob, JobPhase, JobProgress, JobStatus)
from backend.rag.ingest.jobs.registry import (
    JobRegistry, get_default_job_registry)
from backend.rag.ingest.service import IngestOptions

DEFAULT_WORKERS = 2


class IngestWorker:
    def __init__(self, *, service: Any, origin_store: Any,
                 registry: Optional[JobRegistry] = None,
                 max_workers: int = DEFAULT_WORKERS) -> None:
        if service is None: raise ValueError("service required")
        if origin_store is None: raise ValueError("origin_store required")
        if max_workers <= 0: raise ValueError("max_workers must be > 0")
        self._service = service
        self._origin = origin_store
        self._registry = registry or get_default_job_registry()
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="ingest")
        self._cancel_flags: dict = {}
        self._lock = threading.RLock()
        self._shutdown = False

    @property
    def registry(self) -> JobRegistry:
        return self._registry

    @property
    def _drafts(self):
        from backend.rag.ingest.jobs.draft_store import get_default_draft_store
        return get_default_draft_store()

    def submit_file(self, *, file_path: str, filename: str,
                    kb: str, lang: str = "", size_bytes: int = 0,
                    dry_run: bool = False,
                    cleanup: bool = True) -> IngestJob:
        if not file_path or not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        if not filename: filename = os.path.basename(file_path)
        if size_bytes <= 0:
            try: size_bytes = os.path.getsize(file_path)
            except OSError: size_bytes = 0
        job = self._registry.create(filename=filename, kb=kb,
                                     size_bytes=size_bytes, lang=lang)
        with self._lock:
            self._cancel_flags[job.job_id] = False
        # [SUBMIT_HOOKS] 清锁 + 尝试 pipeline（默认关闭）
        from backend.rag.ingest.jobs.submit_hooks import before_submit
        if before_submit(self, job, file_path=file_path,
                         filename=filename, kb=kb, lang=lang):
            return job
        self._pool.submit(self._run_job, job.job_id, file_path,
                          filename, kb, lang, dry_run, cleanup)
        return job

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._cancel_flags: return False
            self._cancel_flags[job_id] = True
        return True

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            self._shutdown = True
        self._pool.shutdown(wait=wait)

    def is_alive(self) -> bool:
        with self._lock:
            return not self._shutdown

    # ---------- 内部 ----------
    def _is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            return bool(self._cancel_flags.get(job_id, False))

    def _update(self, job_id: str, phase: JobPhase, *,
                current: int = 0, total: int = 0, indexed: int = 0,
                message: str = "", detail: Optional[dict] = None) -> None:
        try:
            p = JobProgress(phase=phase, current=current, total=total,
                             indexed=indexed, message=message)
            cur = self._registry.get(job_id)
            if cur is None: return
            if cur.status == JobStatus.PENDING:
                cur = self._registry.update(
                    cur.with_status(JobStatus.RUNNING))
            self._registry.update_progress(job_id, p)
            try:
                self._registry.append_step(job_id, phase,
                                            message=message,
                                            detail=detail or {})
            except Exception as e:
                swallow("rag.ingest.jobs.worker:103", e)
        except Exception as e:
            swallow("rag.ingest.jobs.worker:105", e)

    def _run_job(self, job_id: str, file_path: str, filename: str,
                  kb: str, lang: str, dry_run: bool,
                  cleanup: bool) -> None:
        origin_hash = ""
        try:
            if self._is_cancelled(job_id):
                self._finish_cancelled(job_id); return

            # 阶段 1：保存原件
            self._update(job_id, JobPhase.SAVING, message="保存原件...",
                          detail={"file_path": file_path, "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0})
            try:
                o = self._origin.put_file(file_path,
                                           original_name=filename)
                origin_hash = o.get("hash", "")
            except Exception:
                origin_hash = ""

            if self._is_cancelled(job_id):
                self._finish_cancelled(job_id); return

            # 阶段 2：解析 + 切块 + 索引（service 一体化）
            self._update(job_id, JobPhase.PARSING,
                          message="解析并索引中...",
                          detail={"kb": kb, "lang": lang or "(auto)",
                                  "dry_run": dry_run})
            src = filename
            if origin_hash: src = f"{filename}|origin:{origin_hash}"

            def _on_page(cur: int, total: int):
                self._update(job_id, JobPhase.PARSING,
                              current=cur, total=total,
                              message=f"OCR {cur}/{total} 页")
                # [WD] 通知超时看门狗
                try:
                    from backend.rag.ingest.jobs.job_watchdog import (
                        get_tracker)
                    get_tracker().on_progress(
                        job_id, "ocr", cur, total)
                except Exception:
                    pass

            opts = IngestOptions(
                kb=(kb or "general").strip() or "general",
                source=src, batch_size=64, dry_run=bool(dry_run),
                on_progress=_on_page,
                extra_meta={"job_id": job_id})

            # 审核门：只解析 + 分块，不索引
            chunks = self._service.parse_chunks(file_path, options=opts)
            if not chunks:
                self._registry.finish(
                    job_id, status=JobStatus.FAILED,
                    error="无有效内容（解析/OCR 无输出）",
                    origin_hash=origin_hash)
                return

            # 转草稿并落盘
            from backend.rag.ingest.jobs.review_contracts import DraftChunk
            drafts = [DraftChunk(
                chunk_id=c.chunk_id, text=c.text,
                source=c.source, source_path=c.source_path,
                line_no=c.line_no, role=c.role,
                images=tuple(i.to_dict() for i in c.images),
                metadata=dict(c.metadata)) for c in chunks]
            draft_path = self._drafts.write(job_id, drafts)

            self._update(job_id, JobPhase.FINALIZING,
                          message=f"切分完成：{len(drafts)} 块 → 准备向量化",
                          detail={"draft_count": len(drafts),
                                  "draft_path": draft_path})
            # 用 with_draft 设置待审核态
            cur = self._registry.get(job_id)
            if cur is not None:
                self._registry.update(cur.with_draft(draft_path, len(drafts)))

        except Exception as e:
            self._registry.finish(
                job_id, status=JobStatus.FAILED,
                error=f"{type(e).__name__}: {e}",
                origin_hash=origin_hash)
        finally:
            with self._lock:
                self._cancel_flags.pop(job_id, None)
            if cleanup:
                try: os.unlink(file_path)
                except OSError: pass

    def _finish_cancelled(self, job_id: str) -> None:
        try:
            self._registry.finish(job_id, status=JobStatus.CANCELLED,
                                   error="用户取消")
        except Exception as e:
            swallow("rag.ingest.jobs.worker:191", e)


_WORKER: Optional[IngestWorker] = None


def get_default_worker(service=None,
                        origin_store=None) -> Optional[IngestWorker]:
    global _WORKER
    if _WORKER is None and service is not None and origin_store is not None:
        _WORKER = IngestWorker(service=service, origin_store=origin_store)
    return _WORKER


def set_default_worker(w: Optional[IngestWorker]) -> None:
    global _WORKER
    _WORKER = w


__all__ = ["IngestWorker", "get_default_worker", "set_default_worker",
           "DEFAULT_WORKERS"]
