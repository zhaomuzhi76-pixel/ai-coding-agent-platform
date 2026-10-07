"""断点续跑主入口（向后兼容层）。

职责：
  - resume_all：列出待续跑 job → 逐个 approve
  - 向后兼容：重导出 approve_job_resumable / helpers

消费者：
  - api/rag/ingest_runtime.py → resume_all
  - api/rag/jobs_router.py    → approve_job_resumable
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List

# 向后兼容：重导出（无重复逻辑，只是 import）
from backend.rag.ingest.jobs.resume_helpers import (
    get_embed_offset, set_embed_offset,
    _read_jsonl, _extract, _fail,
    OFFSET_KEY,
)
from backend.rag.ingest.jobs.resume_approve import approve_job_resumable

logger = logging.getLogger(__name__)

def list_resumable_jobs(registry: Any) -> List[str]:
    out: List[str] = []
    try:
        for j in registry.list_recent(limit=100):
            st = getattr(j.status, "name", "").lower()
            if st in ("pending", "running", "pending_review"):
                out.append(j.job_id)
    except Exception:
        pass
    return out


__all__ = ["approve_job_resumable", "get_embed_offset",
           "set_embed_offset", "list_resumable_jobs"]


# ═══════════════ [RESUME_ALL] 自动续跑 ═══════════════
def resume_all(worker: Any) -> dict:
    """扫所有未完成 job，对每个尝试 approve_job_resumable 续跑。
    只处理：
      - status=pending / running / pending_review
      - status=failed 且 draft_path 存在（可续）
    返回 {scanned, resumed, failed}
    """
    import logging as _lg
    import threading as _th
    logger = _lg.getLogger(__name__)
    result = {"scanned": 0, "resumed": 0, "failed": 0, "skipped": 0}

    try:
        jobs = worker.registry.list_recent(limit=100)
    except Exception as e:
        logger.warning("[resume_all] 扫描失败: %r", e)
        return result

    for j in jobs:
        result["scanned"] += 1
        st = getattr(j.status, "name", str(j.status)).lower()
        jid = getattr(j, "job_id", "")

        # [PIPELINE_GUARD] pipeline 启用时，非 failed 交给 pipeline 管
        import os as _os_g
        if _os_g.environ.get("RAG_PIPELINE_ENABLED", "0") == "1" \
                and st in ("pending", "running", "pending_review"):
            result["skipped"] += 1
            continue

        # 只处理可续跑状态
        if st in ("pending", "running", "pending_review"):
            pass
        elif st == "failed":
            # failed 且有 draft_path → 允许续跑
            draft = getattr(j, "draft_path", "") or ""
            if not draft:
                result["skipped"] += 1
                continue
        else:
            # done / cancelled / rejected 跳过
            result["skipped"] += 1
            continue

        # 每个 job 后台线程跑，避免阻塞
        def _bg(jid_=jid):
            try:
                # 先把 failed 恢复成 pending_review 允许续跑
                try:
                    from backend.rag.ingest.jobs.registry import (
                        JobStatus as _JS)
                    j2 = worker.registry.get(jid_)
                    if j2 is not None:
                        st2 = getattr(j2.status, "name", "").lower()
                        if st2 == "failed":
                            worker.registry.finish(
                                jid_, status=_JS.PENDING_REVIEW,
                                chunks_indexed=0,
                                error="auto-resume-from-failed")
                except Exception:
                    pass

                r = approve_job_resumable(worker, jid_, None)
                s = r.get("status", "?")
                if r.get("approved") or s == "done":
                    logger.info("[resume_all] ✅ %s → %s", jid_, s)
                else:
                    logger.warning("[resume_all] ⚠ %s: %s",
                                   jid_, r.get("error", s)[:100])
            except Exception as e:
                logger.warning("[resume_all] ❌ %s: %r", jid_, e)

        _th.Thread(target=_bg, daemon=True, name=f"resume-{jid}").start()
        result["resumed"] += 1

    logger.info("[resume_all] 扫描 %d, 续跑 %d, 跳过 %d",
                result["scanned"], result["resumed"], result["skipped"])
    return result


__all__ = ["approve_job_resumable", "get_embed_offset",
           "set_embed_offset", "resume_all"]
