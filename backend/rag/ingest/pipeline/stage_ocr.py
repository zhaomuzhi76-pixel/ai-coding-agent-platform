"""OCR 阶段：单 worker 串行，独占 GPU。
  queue.dequeue('ocr') → parse_chunks → draft_store.write → enqueue('embed')
依赖注入：service / draft_store。不 import 具体实现。
"""
from __future__ import annotations
import logging
import threading
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class OcrStage:
    def __init__(self, queue: Any, budget: Any,
                 service: Any, draft_store: Any, *,
                 registry: Any = None,
                 poll_interval: float = 1.0,
                 make_options: Optional[Callable] = None) -> None:
        self._q = queue
        self._budget = budget
        self._service = service
        self._drafts = draft_store
        self._registry = registry
        self._poll = poll_interval
        self._make_options = make_options
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def run_once(self) -> bool:
        item = self._q.dequeue("ocr")
        if not item:
            return False
        rid = item["id"]
        job_id = item["job_id"]
        pl = item["payload"]
        # [LEVEL] 从 payload 取分级（缺则 light 兜底）
        level = str(pl.get("level") or "light")
        page_count = int(pl.get("page_count") or 0)
        size_bytes = int(pl.get("size_bytes") or 0)
        # [ADMISSION_V2] 真实资源探测 + 需求估算 → 判决
        from backend.rag.ingest.pipeline.resource_probe import probe
        from backend.rag.ingest.pipeline.job_resource_estimator import estimate
        from backend.rag.ingest.pipeline.admission_policy import (
            evaluate as _admit)
        demand = estimate(page_count=page_count,
                          size_bytes=size_bytes, level=level)
        snapshot = probe()
        decision = _admit(snapshot, demand)
        if not decision.allow:
            self._q.fail(rid, "admission_denied:" + ",".join(decision.reasons[:3]))
            self._q.enqueue(job_id, "ocr", payload=pl, priority=1)
            return True
        # [LEDGER] 注册到账本
        self._budget.register_ocr(job_id, level)
        try:
            file_path = pl.get("file_path", "")
            filename = pl.get("filename", "")
            kb = pl.get("kb", "general")
            lang = pl.get("lang", "")
            if not file_path:
                raise ValueError("payload.file_path required")
            opts = None
            if self._make_options:
                opts = self._make_options(
                    job_id=job_id, file_path=file_path,
                    filename=filename, kb=kb, lang=lang)
            # [REG_RUNNING] 状态 → RUNNING
            if self._registry is not None:
                try:
                    from backend.rag.ingest.jobs.contracts import JobStatus as _JS
                    cur = self._registry.get(job_id)
                    if cur is not None:
                        self._registry.update(cur.with_status(_JS.RUNNING))
                except Exception:
                    pass
            print(f"[ocr-stage] job={job_id} level={level} 开始解析 file={filename}",
                  flush=True)
            chunks = self._service.parse_chunks(file_path, options=opts)
            if not chunks:
                raise RuntimeError("解析结果为空")
            # [FIX] MultimodalChunk → DraftChunk（与 worker.py 保持一致）
            from backend.rag.ingest.jobs.review_contracts import DraftChunk
            drafts = [DraftChunk(
                chunk_id=c.chunk_id, text=c.text,
                source=getattr(c, "source", "") or "",
                source_path=getattr(c, "source_path", "") or "",
                line_no=int(getattr(c, "line_no", 0) or 0),
                role=getattr(c, "role", "") or "",
                images=tuple(i.to_dict() for i in (getattr(c, "images", ()) or ())),
                metadata=dict(getattr(c, "metadata", {}) or {}),
            ) for c in chunks]
            draft_path = self._drafts.write(job_id, drafts)
            # [REG_DRAFT] 写 draft_path 到 registry
            if self._registry is not None:
                try:
                    cur = self._registry.get(job_id)
                    if cur is not None:
                        self._registry.update(
                            cur.with_draft(draft_path, len(drafts)))
                except Exception:
                    pass
            self._q.enqueue(job_id, "embed",
                            payload={"draft_path": draft_path,
                                     "total": len(chunks)},
                            priority=0)
            self._q.complete(rid)
            print(f"[ocr-stage] job={job_id} ✅ chunks={len(chunks)} draft={draft_path}", flush=True)
        except Exception as e:
            logger.error("[ocr-stage] job=%s 失败: %r", job_id, e)
            self._q.fail(rid, f"{type(e).__name__}: {e}")
        finally:
            # [LEDGER] 从账本注销（原 release_ocr）
            self._budget.unregister_ocr(job_id)
        return True

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if not self.run_once():
                    self._stop.wait(self._poll)
            except Exception as e:
                logger.error("[ocr-stage] loop 异常: %r", e)
                time.sleep(1.0)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop,
                                        name="pipeline-ocr", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)


__all__ = ["OcrStage"]
