"""Job 磁盘持久化辅助。职责：JSON 文件读/写/删 + 历史清理。
不做业务、不做序列化（_serde 管）。_ 前缀表示内部模块。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import json
from pathlib import Path
from typing import Optional

from backend.rag.ingest.jobs.contracts import IngestJob


def save_job(root: Path, job: IngestJob) -> None:
    """原子写：临时文件 → replace。失败静默（不影响主流程）。"""
    try:
        root.mkdir(parents=True, exist_ok=True)
        p = root / f"{job.job_id}.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(job.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8")
        tmp.replace(p)
    except Exception as e:
        swallow("rag.ingest.jobs._persist:25", e, level="error")


def delete_job(root: Path, job_id: str) -> None:
    try:
        p = root / f"{job_id}.json"
        if p.exists():
            p.unlink()
    except Exception as e:
        swallow("rag.ingest.jobs._persist:34", e, level="error")


def cleanup_oldest(root: Path, max_history: int) -> None:
    """超过 max_history 时删最旧的。"""
    try:
        files = sorted(root.glob("job-*.json"),
                       key=lambda p: p.stat().st_mtime)
        while len(files) > max_history:
            old = files.pop(0)
            try: old.unlink()
            except Exception: pass
    except Exception as e:
        swallow("rag.ingest.jobs._persist:47", e, level="error")


def load_all(root: Path) -> list:
    """读取根目录下所有 job-*.json。返回 [(dict), ...]。"""
    if not root.exists():
        return []
    out: list = []
    for p in root.glob("job-*.json"):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


__all__ = ["save_job", "delete_job", "cleanup_oldest", "load_all"]
