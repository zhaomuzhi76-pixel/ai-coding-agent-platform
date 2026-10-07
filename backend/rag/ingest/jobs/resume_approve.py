"""approve_job_resumable：断点续跑 + 完整性门禁。

职责：
  - L1 校验（draft 完整）
  - 索引到向量库（分批）
  - L3 校验（count == draft 行数）
  - 失败 → 全清该 job
不做：
  - helpers 在 resume_helpers.py
  - resume_all 在 resume_support.py
"""
from __future__ import annotations
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.rag.ingest.jobs import integrity as _it
from backend.rag.ingest.jobs.resume_helpers import (
    get_embed_offset, set_embed_offset,
    _read_jsonl, _extract, _fail,
    OFFSET_KEY,
)

logger = logging.getLogger(__name__)

def approve_job_resumable(worker: Any, job_id: str,
                          body: Optional[dict] = None) -> Dict[str, Any]:
    from backend.rag.ingest.jobs.registry import (
        JobStatus as JS, JobProgress, JobPhase)
    result: Dict[str, Any] = {"approved": False, "job_id": job_id,
                              "status": "unknown"}
    try:
        j = worker.registry.get(job_id)
        if j is None:
            result["error"] = "job not found"; return result
        cur = getattr(j.status, "name", str(j.status)).lower()
        result["status"] = cur
        if cur in ("done", "cancelled", "rejected"):
            result["note"] = "terminal"; return result

        draft = getattr(j, "draft_path", "") or ""
        if not draft or not os.path.isfile(draft):
            _fail(worker.registry, job_id, "draft_path missing")
            result["error"] = "draft_path missing"; return result

        # ═══ L1: 入库前完整性校验 ═══
        total_hint = int((getattr(j, "progress", None) and
                          getattr(j.progress, "total", 0)) or 0)
        ok1, r1 = _it.validate_before_ingest(draft, total_hint=0)
        if not ok1:
            err = f"L1 draft 不完整: {r1['errors'][:3]}"
            _fail(worker.registry, job_id, err)
            result["error"] = err; return result
        chunks = r1["chunks"]
        logger.info("[integrity] L1 通过: draft=%d 行", r1["n_lines"])

        texts, ids, metas = _extract(chunks, job_id, j)
        total = len(texts)
        if total != r1["n_lines"]:
            err = f"L1 校验后数量异常: {total} != {r1['n_lines']}"
            _fail(worker.registry, job_id, err)
            result["error"] = err; return result

        # ═══ embed 引擎 ═══
        try:
            from backend.api.rag.ingest_runtime import get_ingest_runtime
            ef = getattr(get_ingest_runtime(), "embed_fn", None)
        except Exception:
            ef = None
        if not callable(ef):
            result["error"] = "embed_fn not callable"; return result
        if hasattr(ef, "warmup"):
            try: ef.warmup()
            except Exception: pass

        # ═══ 向量库 + 反查真实状态 ═══
        from backend.storage.vector_backend import get_vector_store
        from backend.storage.vector_config import VectorConfig
        vs = get_vector_store(VectorConfig())

        # L2: 反查真实 offset（不信内存）
        offset = _it.actual_offset(vs, job_id, ids)
        stored_ids = _it.list_stored_ids(vs, job_id)
        logger.info("[integrity] L2 反查: 库内=%d, 真实 offset=%d, "
                    "draft=%d", len(stored_ids), offset, total)

        if offset > 0 and offset < total:
            # 断点续传
            logger.info("[resume] 从 %d/%d 继续", offset, total)
        elif offset >= total:
            # 已全部入库
            logger.info("[resume] 已全部入库 (%d)，直接校验", total)
        else:
            # 从头
            offset = 0

        # ═══ 幂等清理：从头跑时，先清空该 job 老数据 ═══
        if offset == 0:
            n_del = _it.clear_job_data(vs, job_id)
            if n_del:
                logger.info("[integrity] 幂等清理 %d 条旧数据", n_del)

        BATCH = int(os.environ.get("RAG_EMBED_BATCH", "8"))
        RETRY = 3
        inserted = offset

        # ═══ 分批写入 ═══
        for _i in range(offset, total, BATCH):
            _txt = texts[_i:_i + BATCH]
            _ids = ids[_i:_i + BATCH]
            _mts = [dict(m, _job_pending=True, _job_id=job_id) for m in metas[_i:_i + BATCH]]

            embs = None; err = None
            for _try in range(RETRY):
                try:
                    embs = ef(_txt); err = None; break
                except Exception as e:
                    err = e
                    if _try < RETRY - 1:
                        time.sleep(1.0 * (_try + 1))
            if embs is None:
                raise RuntimeError(f"batch {_i} embed failed: {err!r}")

            vs.add_documents(documents=_txt, ids=_ids,
                             metadata=_mts, embeddings=embs)
            inserted = _i + len(_txt)
            set_embed_offset(worker.registry, job_id, inserted)

            try:
                worker.registry.update_progress(job_id, JobProgress(
                    phase=JobPhase.EMBEDDING,
                    current=inserted, total=total,
                    message=f"向量化 {inserted}/{total} 块"))
            except Exception:
                pass
            # [WD] 通知超时看门狗
            try:
                from backend.rag.ingest.jobs.job_watchdog import (
                    get_tracker)
                get_tracker().on_progress(
                    job_id, "embedding", inserted, total)
            except Exception:
                pass

        # ═══ L3: 入库后完整性校验 ═══
        ok3, r3 = _it.validate_after_ingest(vs, job_id, ids)
        if not ok3:
            err = (f"L3 校验失败: stored={r3['n_stored']} "
                   f"expected={r3['n_expected']} "
                   f"missing={r3['n_missing']} extra={r3['n_extra']}")
            logger.error("[integrity] %s", err)
            _it.clear_job_data(vs, job_id)   # 回滚：全清
            _fail(worker.registry, job_id, err)
            result["error"] = err; return result
        logger.info("[integrity] L3 通过: %d 条完整", r3["n_stored"])

        # ═══ 原子可见：翻转 _job_pending=false ═══
        try:
            if hasattr(vs, "_conn"):
                cur2 = vs._conn.execute("SELECT id, metadata FROM docs")
                n_flip = 0
                for _id, _mj in cur2.fetchall():
                    try: _m = json.loads(_mj or "{}")
                    except: continue
                    if _m.get("job_id") == job_id and _m.get("_job_pending"):
                        _m["_job_pending"] = False
                        vs._conn.execute(
                            "UPDATE docs SET metadata=? WHERE id=?",
                            (json.dumps(_m, ensure_ascii=False), _id))
                        n_flip += 1
                vs._conn.commit(); vs._cache = None
                logger.info("[integrity] 翻转 %d 条 → 可见", n_flip)
        except Exception as e:
            logger.warning("[integrity] 翻转失败: %r", e)

        # [GPU_RELEASE] 任务完成 → 主动释放显存（Paddle + Ollama）
        try:
            from backend.rag.ingest.parsers.pdf_ocr_parser_batch import (
                _release_gpu_memory)
            _release_gpu_memory()
            logger.info("[integrity] Paddle 显存已释放")
        except Exception:
            pass
        try:
            from backend.providers.runtime.ollama_embed import unload_model
            if unload_model():
                logger.info("[integrity] Ollama 模型已卸载")
        except Exception:
            pass

        _done = getattr(JS, "DONE", None)
        worker.registry.finish(job_id, status=_done,
                               chunks_indexed=inserted, error="")
        result.update({"approved": True, "status": "done",
                       "chunks_indexed": inserted,
                       "n_verified": r3["n_stored"]})
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        _fail(worker.registry, job_id, f"{type(e).__name__}: {e}")
        result["error"] = f"{type(e).__name__}: {e}"
        return result


