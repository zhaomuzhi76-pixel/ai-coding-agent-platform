"""PipelineScheduler：三阶段流水线装配与生命周期。
职责：注入依赖 → 启停三阶段 → 暴露 submit_job 入队接口。
不实现执行（stage_* 管）、不实现队列（queue 管）。
环境变量：
  RAG_PIPELINE_EMBED_WORKERS=3
  RAG_PIPELINE_EMBED_BATCH=16
  RAG_PIPELINE_ENABLED=1    为 0 时 sched 不启动（兼容旧路径）
"""
from __future__ import annotations
import logging
import os
from typing import Any, Callable, Dict, Optional

from backend.rag.ingest.pipeline.queue import PipelineQueue
from backend.rag.ingest.pipeline.resource_budget import get_budget
from backend.rag.ingest.pipeline.stage_ocr import OcrStage
from backend.rag.ingest.pipeline.stage_embed import EmbedStage
from backend.rag.ingest.pipeline.stage_vecwrite import VecWriteStage
from backend.rag.ingest.pipeline.idle_reaper import IdleReaper

logger = logging.getLogger(__name__)


class PipelineScheduler:
    def __init__(self, *,
                 service: Any,
                 draft_store: Any,
                 embed_fn: Any,
                 vector_store: Any,
                 on_job_done: Optional[Callable[[str], None]] = None,
                 make_options: Optional[Callable] = None,
                 registry: Any = None,
                 db_path: Optional[str] = None) -> None:
        self._q = PipelineQueue(db_path)
        self._registry = registry
        self._budget = get_budget()
        self._ocr = OcrStage(self._q, self._budget, service, draft_store,
                             registry=registry,
                             make_options=make_options)
        embed_workers = int(os.environ.get("RAG_PIPELINE_EMBED_WORKERS", "3"))
        embed_batch = int(os.environ.get("RAG_PIPELINE_EMBED_BATCH", "16"))
        self._embed = EmbedStage(self._q, self._budget, embed_fn,
                                 draft_store,
                                 workers=embed_workers,
                                 batch_size=embed_batch)
        self._vw = VecWriteStage(self._q, vector_store,
                                 on_job_done=on_job_done)
        self._reaper = IdleReaper(self._q, registry) if registry else None
        self._started = False

    @property
    def queue(self) -> PipelineQueue:
        return self._q

    def enabled(self) -> bool:
        return os.environ.get("RAG_PIPELINE_ENABLED", "1") != "0"

    def submit_job(self, job_id: str, *, file_path: str, filename: str,
                   kb: str = "general", lang: str = "",
                   priority: int = 0) -> int:
        return self._q.enqueue(
            job_id, "ocr",
            payload={"file_path": file_path, "filename": filename,
                     "kb": kb, "lang": lang},
            priority=priority)

    def recover(self) -> int:
        """断电恢复：running → pending。"""
        n = self._q.recover_running()
        if n:
            logger.info("[scheduler] 断电恢复: %d 条 running → pending", n)
        return n

    def start(self) -> None:
        if self._started or not self.enabled():
            return
        self._ocr.start()
        self._embed.start()
        self._vw.start()
        if self._reaper is not None:
            self._reaper.start()
        self._started = True
        logger.info("[scheduler] 三阶段已启动: ocr=1, embed=%d, vecwrite=1",
                    self._embed._workers)

    def stop(self, timeout: float = 5.0) -> None:
        if not self._started:
            return
        if self._reaper is not None:
            self._reaper.stop(timeout)
        self._vw.stop(timeout)
        self._embed.stop(timeout)
        self._ocr.stop(timeout)
        self._started = False
        logger.info("[scheduler] 三阶段已停止")

    def stats(self) -> Dict[str, Any]:
        return {"started": self._started,
                "queue": self._q.stats(),
                "budget": self._budget.snapshot()}


_SCHED: Optional[PipelineScheduler] = None


def get_scheduler() -> Optional[PipelineScheduler]:
    return _SCHED


def set_scheduler(s: Optional[PipelineScheduler]) -> None:
    global _SCHED
    _SCHED = s


__all__ = ["PipelineScheduler", "get_scheduler", "set_scheduler"]
