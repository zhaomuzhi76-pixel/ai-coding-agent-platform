"""断点续跑的共享 helper（纯函数，无业务逻辑）。

职责：
  - offset 读写（内存兼容）
  - JSONL 读取 / draft 抽取
  - 失败标记
不做：
  - approve / resume 编排（resume_approve / resume_support 管）
"""

from __future__ import annotations
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.rag.ingest.jobs import integrity as _it

logger = logging.getLogger(__name__)

OFFSET_KEY = "embed_offset"


# ═══════════════ 内存 offset（兼容旧接口，但不再信任） ═══════════════
def get_embed_offset(job: Any) -> int:
    try:
        return int((getattr(job, "meta", {}) or {}).get(OFFSET_KEY, 0))
    except Exception:
        return 0


def set_embed_offset(registry: Any, job_id: str, offset: int) -> None:
    """[FROZEN_FIX] IngestJob 是 frozen dataclass → 用 dataclasses.replace
    生成新对象，再 registry.update(new_job)。
    """
    try:
        j = registry.get(job_id)
        if j is None:
            return
        m = dict(getattr(j, "meta", {}) or {})
        m[OFFSET_KEY] = int(offset)

        # 优先用 registry.update(job) 接口
        if hasattr(registry, "update"):
            from dataclasses import replace as _dc_replace
            new_job = _dc_replace(j, meta=m)
            registry.update(new_job)
            return

        # 兜底 1：registry.update_meta
        if hasattr(registry, "update_meta"):
            registry.update_meta(job_id, m)
            return

        # 兜底 2：last resort（会失败，但至少打日志）
        logger.warning(
            "[resume] set_embed_offset: registry 无 update/update_meta，"
            "offset=%d 无法持久化", offset)
    except Exception as e:
        logger.warning("[resume] set_embed_offset 失败: %r", e)


# ═══════════════ 工具 ═══════════════
def _read_jsonl(path: str) -> List[dict]:
    out: List[dict] = []
    p = Path(path)
    if not p.is_file():
        return out
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _extract(chunks: List[dict], job_id: str, job: Any
             ) -> Tuple[List[str], List[str], List[dict]]:
    """从 chunks 提取 texts/ids/metas。id 使用 chunk_id（全局唯一）。"""
    texts, ids, metas = [], [], []
    oh = getattr(job, "origin_hash", "") or ""
    fn = getattr(job, "filename", "") or ""
    kb = getattr(job, "kb", "default") or "default"
    for i, c in enumerate(chunks):
        if isinstance(c, str):
            txt = c; meta = {}
        else:
            txt = c.get("text") or c.get("content") or ""
            meta = dict(c.get("metadata") or {})
            # [IMG_FIX] 把 images 合并进 metadata（否则检索时看不到图）
            _imgs = c.get("images")
            if _imgs:
                import json as _j
                meta["__images_json__"] = _j.dumps(_imgs, ensure_ascii=False)
        cid = None
        if isinstance(c, dict):
            for k in ("chunk_id", "id", "_id", "uid"):
                if c.get(k):
                    cid = str(c[k]); break
        if not cid:
            cid = f"{job_id}_chunk_{i}"
        if oh:
            meta.setdefault("origin_hash", oh)
        meta.setdefault("job_id", job_id)
        meta.setdefault("filename", fn)
        meta.setdefault("kb", kb)
        texts.append(txt); ids.append(cid); metas.append(meta)
    return texts, ids, metas


def _fail(registry: Any, job_id: str, err: str) -> None:
    try:
        from backend.rag.ingest.jobs.registry import JobStatus
        registry.finish(job_id, status=JobStatus.FAILED, error=err)
    except Exception:
        pass


# ═══════════════ 主入口 ═══════════════
