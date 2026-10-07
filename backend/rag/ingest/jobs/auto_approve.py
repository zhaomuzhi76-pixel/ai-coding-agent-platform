"""自动审核钩子。职责：worker 完成草稿后自动 approve，跳过人工审核。
通过环境变量 RAG_AUTO_APPROVE=1（默认开）控制。
独立插件，不修改 worker 核心逻辑。"""
import os
import logging

logger = logging.getLogger(__name__)

def is_enabled() -> bool:
    return os.environ.get("RAG_AUTO_APPROVE", "1") == "1"


def auto_approve_if_enabled(worker, job_id: str) -> bool:
    """如果开启自动审核，调用 approve_job_safe 落库。返回是否执行。"""
    if not is_enabled():
        return False
    try:
        from backend.rag.ingest.jobs.approve_logic import approve_job_safe
        result = approve_job_safe(worker, job_id, {"accepted_indices": None})
        ok = result.get("approved") or result.get("status") == "done"
        logger.info("[auto-approve] job=%s ok=%s status=%s via=%s",
                    job_id, ok, result.get("status"), result.get("via"))
        return ok
    except Exception as e:
        logger.warning("[auto-approve] job=%s 失败: %r", job_id, e)
        return False


__all__ = ["is_enabled", "auto_approve_if_enabled"]
