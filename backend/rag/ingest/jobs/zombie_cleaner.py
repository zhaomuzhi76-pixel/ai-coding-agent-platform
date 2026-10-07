"""[L5 僵尸清理] 进程 + 数据全清。独立模块，可启动时/定时/手动触发。
安全原则：
  - 只清明确终态/超期的
  - 默认 dry_run=True（预览模式）
  - 保留审计日志
"""
from __future__ import annotations
import json
import logging
import os
import subprocess  # [PRECISE_MATCH]
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 保留期限（天）
KEEP_DRAFT_DAYS = int(os.environ.get("RAG_KEEP_DRAFT_DAYS", "7"))
KEEP_CKPT_DAYS = int(os.environ.get("RAG_KEEP_CKPT_DAYS", "7"))
KEEP_TOMBSTONE_DAYS = int(os.environ.get("RAG_KEEP_TOMBSTONE_DAYS", "30"))
# job 卡死的判定：2 小时无进度（比 L4 的 30 分钟宽松，避免误杀）
STALE_JOB_HOURS = int(os.environ.get("RAG_STALE_JOB_HOURS", "2"))


# ═══════════════ 1. 僵尸进程 ═══════════════
def scan_zombie_processes() -> List[Dict[str, Any]]:
    """[PRECISE_MATCH] 扫重复进程。
    关键修复：
      1. 用正则精确匹配 cmdline 结尾（防误匹配 reranker_server）
      2. 排除自己 PID + 父 PID
      3. 只匹配主后端 + 看门狗
    """
    import os as _os
    import re as _re
    my_pid = _os.getpid()
    my_ppid = _os.getppid()

    # 精确正则
    SPECS = [
        # 主后端：路径 + python[版本] + -m backend 结尾
        (_re.compile(r'^(?:\S+/)?python[0-9.]*\s+-m\s+backend$'),
         'python -m backend'),
        # 看门狗
        (_re.compile(r'^(?:\S+/)?python[0-9.]*\s+\S*gpu_watchdog\.py$'),
         'gpu_watchdog.py'),
    ]

    # 拿所有进程
    try:
        r = subprocess.run(["ps", "-eo", "pid,args"],
                           capture_output=True, text=True, timeout=5)
        lines = r.stdout.strip().split("\n")[1:]
    except Exception:
        return []

    out = []
    for regex, label in SPECS:
        matches = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[0])
            except ValueError:
                continue
            cmd = parts[1].strip()
            # 排除自己/父
            if pid == my_pid or pid == my_ppid:
                continue
            # 精确匹配
            if regex.match(cmd):
                matches.append((pid, cmd))

        if len(matches) > 1:
            infos = []
            for pid, cmd in matches:
                try:
                    with open(f"/proc/{pid}/stat") as f:
                        st = f.read().split()
                    infos.append((pid, float(st[21]), cmd))
                except Exception:
                    infos.append((pid, 0.0, cmd))
            infos.sort(key=lambda x: x[1])
            for pid, _, cmd in infos[:-1]:
                out.append({"pattern": label, "pid": pid, "cmd": cmd})

    return out

def kill_zombie_processes(pids: List[Dict], dry_run: bool = True) -> int:
    """杀僵尸进程。"""
    n = 0
    for item in pids:
        pid = item["pid"]
        if dry_run:
            logger.info("[zombie-proc] dry_run 将杀 PID=%d (%s)",
                        pid, item["pattern"])
        else:
            try:
                os.kill(pid, 9)
                logger.warning("[zombie-proc] 杀 PID=%d (%s)",
                               pid, item["pattern"])
                n += 1
            except Exception as e:
                logger.debug("kill %d: %r", pid, e)
    return n


# ═══════════════ 2. 僵尸 job ═══════════════
def scan_zombie_jobs(registry: Any) -> List[Dict]:
    """job.status=RUNNING/PENDING_REVIEW 但 > STALE_JOB_HOURS 无进度。"""
    from backend.rag.ingest.jobs.registry import JobStatus
    out = []
    now = time.time()
    cutoff = now - STALE_JOB_HOURS * 3600
    try:
        for j in registry.list_recent(limit=500):
            st = getattr(j.status, "name", "").lower()
            if st not in ("running", "pending_review", "pending"):
                continue
            # 检查最后更新时间
            last = max(
                getattr(j, "finished_at", 0) or 0,
                getattr(j, "started_at", 0) or 0,
                getattr(j, "created_at", 0) or 0,
            )
            # 或从 progress 里取
            prog = getattr(j, "progress", None)
            if prog:
                last = max(last, getattr(prog, "updated_at", 0) or 0)
            if last < cutoff:
                out.append({
                    "job_id": j.job_id,
                    "status": st,
                    "last_update": last,
                    "stale_hours": (now - last) / 3600,
                    "filename": getattr(j, "filename", ""),
                })
    except Exception as e:
        logger.warning("[zombie-job] 扫描失败: %r", e)
    return out


def mark_zombie_jobs_failed(registry: Any, jobs: List[Dict],
                             dry_run: bool = True) -> int:
    """标记僵尸 job 为 failed。"""
    from backend.rag.ingest.jobs.registry import JobStatus
    n = 0
    for item in jobs:
        jid = item["job_id"]
        if dry_run:
            logger.info("[zombie-job] dry_run 将标记 %s (%.1fh 无更新) → failed",
                        jid, item["stale_hours"])
        else:
            try:
                registry.finish(jid, status=JobStatus.FAILED,
                                error=f"stale {item['stale_hours']:.1f}h",
                                chunks_indexed=0)
                logger.warning("[zombie-job] %s → failed", jid)
                n += 1
            except Exception as e:
                logger.debug("mark %s: %r", jid, e)
    return n


# ═══════════════ 3. 僵尸 draft ═══════════════
def scan_zombie_drafts(draft_root: str) -> List[Dict]:
    """draft 文件 > KEEP_DRAFT_DAYS 天。"""
    out = []
    p = Path(draft_root)
    if not p.is_dir():
        return out
    now = time.time()
    cutoff = now - KEEP_DRAFT_DAYS * 86400
    for f in p.glob("*.jsonl"):
        try:
            mt = f.stat().st_mtime
            if mt < cutoff:
                out.append({
                    "path": str(f),
                    "size_mb": f.stat().st_size / 1024 / 1024,
                    "age_days": (now - mt) / 86400,
                })
        except Exception:
            continue
    return out


def delete_zombie_drafts(items: List[Dict], dry_run: bool = True) -> int:
    n = 0
    for item in items:
        if dry_run:
            logger.info("[zombie-draft] dry_run 将删 %s (%.1f天)",
                        item["path"], item["age_days"])
        else:
            try:
                os.unlink(item["path"])
                n += 1
            except Exception:
                pass
    return n


# ═══════════════ 4. 僵尸 checkpoint ═══════════════
def scan_zombie_checkpoints(ckpt_dir: str) -> List[Dict]:
    """OCR checkpoint > KEEP_CKPT_DAYS 天 或 total_pages 字段缺失。"""
    out = []
    p = Path(ckpt_dir)
    if not p.is_dir():
        return out
    now = time.time()
    cutoff = now - KEEP_CKPT_DAYS * 86400
    for f in p.glob("*.json"):
        try:
            mt = f.stat().st_mtime
            if mt < cutoff:
                out.append({"path": str(f),
                            "age_days": (now - mt) / 86400})
                continue
            # 内容不完整
            data = json.loads(f.read_text(encoding="utf-8"))
            if not data.get("pdf_hash") or not data.get("total_pages"):
                out.append({"path": str(f), "age_days": 0,
                            "reason": "invalid"})
        except Exception:
            continue
    return out


def delete_zombie_checkpoints(items: List[Dict],
                               dry_run: bool = True) -> int:
    n = 0
    for item in items:
        if dry_run:
            logger.info("[zombie-ckpt] dry_run 将删 %s", item["path"])
        else:
            try:
                os.unlink(item["path"])
                n += 1
            except Exception:
                pass
    return n


# ═══════════════ 5. 僵尸 tombstone ═══════════════
def scan_zombie_tombstones() -> List[Dict]:
    """deleted_jobs 表 > KEEP_TOMBSTONE_DAYS 天。"""
    out = []
    try:
        from backend.rag.ingest.jobs.deleted_registry import (
            get_deleted_registry)
        dr = get_deleted_registry()
        if not hasattr(dr, "_conn"):
            return out
        cutoff = time.time() - KEEP_TOMBSTONE_DAYS * 86400
        cur = dr._conn.execute(
            "SELECT job_id, deleted_at FROM deleted WHERE deleted_at < ?",
            (cutoff,))
        for jid, dt in cur.fetchall():
            out.append({"job_id": jid, "age_days": (time.time() - dt) / 86400})
    except Exception as e:
        logger.debug("[zombie-tomb] 扫描失败: %r", e)
    return out


def delete_zombie_tombstones(items: List[Dict],
                              dry_run: bool = True) -> int:
    n = 0
    if not items:
        return 0
    try:
        from backend.rag.ingest.jobs.deleted_registry import (
            get_deleted_registry)
        dr = get_deleted_registry()
        if not hasattr(dr, "_conn"):
            return 0
        for item in items:
            if dry_run:
                logger.info("[zombie-tomb] dry_run 将删 %s (%.1f天)",
                            item["job_id"], item["age_days"])
            else:
                dr._conn.execute("DELETE FROM deleted WHERE job_id=?",
                                 (item["job_id"],))
                n += 1
        if not dry_run:
            dr._conn.commit()
    except Exception:
        pass
    return n


# ═══════════════ 6. 僵尸向量（_job_pending 但 job 已终态/不存在）═══════════════
def scan_zombie_vectors(vs: Any, registry: Any) -> List[Dict]:
    """向量库里 _job_pending=true 但 job 已 failed/cancelled/不存在。"""
    out = []
    try:
        if not hasattr(vs, "_conn"):
            return out
        from collections import Counter
        # 先按 job_id 分组 pending 数量
        cur = vs._conn.execute("SELECT id, metadata FROM docs")
        by_job = Counter()
        for id_, meta_str in cur.fetchall():
            try:
                m = json.loads(meta_str or "{}")
            except Exception:
                continue
            if m.get("_job_pending"):
                by_job[m.get("job_id", "?")] += 1

        for jid, n in by_job.items():
            if jid == "?":
                out.append({"job_id": jid, "n": n, "reason": "no_job_id"})
                continue
            j = registry.get(jid)
            if j is None:
                out.append({"job_id": jid, "n": n, "reason": "job_missing"})
                continue
            st = getattr(j.status, "name", "").lower()
            if st in ("failed", "cancelled", "rejected"):
                out.append({"job_id": jid, "n": n,
                            "reason": f"job_{st}"})
    except Exception as e:
        logger.warning("[zombie-vec] 扫描失败: %r", e)
    return out


def delete_zombie_vectors(vs: Any, items: List[Dict],
                           dry_run: bool = True) -> int:
    n = 0
    if not items or not hasattr(vs, "_conn"):
        return 0
    target_jobs = {x["job_id"] for x in items}
    try:
        cur = vs._conn.execute("SELECT id, metadata FROM docs")
        for id_, meta_str in cur.fetchall():
            try:
                m = json.loads(meta_str or "{}")
            except Exception:
                continue
            jid = m.get("job_id", "?")
            if not m.get("_job_pending"):
                continue
            if jid in target_jobs or jid == "?":
                if dry_run:
                    logger.info("[zombie-vec] dry_run 将删 %s (job=%s)",
                                id_, jid)
                else:
                    vs._conn.execute("DELETE FROM docs WHERE id=?", (id_,))
                    n += 1
        if not dry_run:
            vs._conn.commit()
            vs._cache = None
    except Exception:
        pass
    return n


# ═══════════════ 主入口 ═══════════════
_ctx: Dict[str, Any] = {}


def full_scan(dry_run: bool = True, worker=None) -> Dict[str, Any]:
    """worker: 可选传入，避免在 worker 构建时递归调用 get_worker()"""
    if worker is not None:
        _ctx["worker"] = worker
    """全量扫描/清理。返回统计。"""
    result = {
        "dry_run": dry_run,
        "started_at": datetime.now().isoformat(),
        "processes": {}, "jobs": {}, "drafts": {},
        "checkpoints": {}, "tombstones": {}, "vectors": {},
    }
    # 1. 进程
    procs = scan_zombie_processes()
    result["processes"] = {
        "found": len(procs),
        "killed": kill_zombie_processes(procs, dry_run) if procs else 0,
        "items": procs[:10],
    }
    # 2. job
    # [NO_RECURSION] 优先用传入的 registry，避免在 _build_worker 里调 get_worker
    try:
        w = _ctx.get("worker")
        if w is None:
            # 延迟导入，且 try 保护（防止从 _build_worker 进来时递归）
            import sys as _sys
            _mod = _sys.modules.get("backend.api.rag.ingest_runtime")
            if _mod is not None and hasattr(_mod, "_WORKER") and _mod._WORKER is not None:
                w = _mod._WORKER
            else:
                # 真没有就走懒加载（正常场景，不是递归入口）
                from backend.api.rag.ingest_runtime import get_worker
                w = get_worker()
        jobs = scan_zombie_jobs(w.registry)
        result["jobs"] = {
            "found": len(jobs),
            "marked": mark_zombie_jobs_failed(w.registry, jobs, dry_run) if jobs else 0,
            "items": jobs[:10],
        }
        # 6. 向量
        try:
            from backend.storage.vector_backend import get_vector_store
            from backend.storage.vector_config import VectorConfig
            vs = get_vector_store(VectorConfig())
            vecs = scan_zombie_vectors(vs, w.registry)
            result["vectors"] = {
                "found": len(vecs),
                "deleted": delete_zombie_vectors(vs, vecs, dry_run) if vecs else 0,
                "items": vecs[:10],
            }
        except Exception as e:
            result["vectors"] = {"error": str(e)}
    except Exception as e:
        result["jobs"] = {"error": str(e)}
    # 3. draft
    draft_root = os.path.expanduser("~/.cache/agent_knowledge/drafts")
    drafts = scan_zombie_drafts(draft_root)
    result["drafts"] = {
        "found": len(drafts),
        "deleted": delete_zombie_drafts(drafts, dry_run) if drafts else 0,
        "items": drafts[:10],
    }
    # 4. checkpoint
    ckpt_dir = os.path.expanduser(
        "~/.cache/agent_knowledge/ocr_checkpoints")
    ckpts = scan_zombie_checkpoints(ckpt_dir)
    result["checkpoints"] = {
        "found": len(ckpts),
        "deleted": delete_zombie_checkpoints(ckpts, dry_run) if ckpts else 0,
        "items": ckpts[:10],
    }
    # 5. tombstone
    tombs = scan_zombie_tombstones()
    result["tombstones"] = {
        "found": len(tombs),
        "deleted": delete_zombie_tombstones(tombs, dry_run) if tombs else 0,
        "items": tombs[:10],
    }
    result["finished_at"] = datetime.now().isoformat()
    return result


__all__ = ["full_scan", "scan_zombie_processes", "scan_zombie_jobs",
           "scan_zombie_drafts", "scan_zombie_checkpoints",
           "scan_zombie_tombstones", "scan_zombie_vectors"]
