"""
职责：清理卡死在 pending_review 的历史僵尸 job（独立插件，不动原状态机）
触发：启动时或手动 API
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
ZOMBIE_AGE_HOURS = 1
TERMINAL_STATES = {"completed", "failed", "approved", "cancelled"}

def clean_zombie_jobs(job_store, dry_run: bool = True) -> dict:
    """
    把超过 ZOMBIE_AGE_HOURS 小时仍为 pending_review 的 job 标记为 failed。
    :param job_store: 主后端原有的 job 存储对象
    :return: 清理统计
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=ZOMBIE_AGE_HOURS)
    cleaned, scanned = [], 0

    for job in list(job_store.list_all()):
        scanned += 1
        if job.get("status") != "pending_review":
            continue
        created = job.get("created_at")
        try:
            created_dt = datetime.fromisoformat(created)
        except Exception:
            continue
        if created_dt < cutoff:
            cleaned.append(job.get("id"))
            if not dry_run:
                job_store.update(job["id"], status="failed",
                                 error="zombie_pending_review_cleaned")
    logger.info("[zombie-cleaner] dry_run=%s scanned=%d cleaned=%d",
                dry_run, scanned, len(cleaned))
    return {"scanned": scanned, "cleaned": cleaned, "dry_run": dry_run}
