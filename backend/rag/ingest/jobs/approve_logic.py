"""纯逻辑：approve job 草稿入库。不抛异常，只返回状态快照。"""
import json, logging, traceback, os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def approve_job_safe(worker: Any, job_id: str,
                     body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from backend.rag.ingest.jobs.registry import JobStatus as JS
    result: Dict[str, Any] = {"approved": False, "job_id": job_id, "status": "unknown"}

    def _recover():
        try:
            j2 = worker.registry.get(job_id)
            s2 = getattr(j2.status, "name", str(j2.status)).lower() if j2 else ""
            if s2 == "done":
                result.update({"approved": True, "status": "done", "recovered": True})
                return True
        except Exception:
            pass
        return False

    try:
        j = worker.registry.get(job_id)
        if j is None:
            result["error"] = "job not found"; return result
        cur = getattr(j.status, "name", str(j.status)).lower()
        result["status"] = cur
        if cur in ("done", "cancelled", "rejected"):
            result["note"] = "已是终态"; return result

        draft = getattr(j, "draft_path", "") or ""
        if not draft or not Path(draft).exists():
            _f = getattr(JS, "FAILED", None)
            if _f: worker.registry.finish(job_id, status=_f, error="draft_path 缺失")
            result["error"] = "draft_path 缺失: " + draft; return result

        chunks = []
        with open(draft, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line: chunks.append(json.loads(line))
        if not chunks:
            _f = getattr(JS, "FAILED", None)
            if _f: worker.registry.finish(job_id, status=_f, error="草稿为空")
            result["error"] = "草稿为空"; return result

        acc = body.get("accepted_indices") if isinstance(body, dict) else None
        if isinstance(acc, list):
            chunks = [chunks[i] for i in acc if 0 <= i < len(chunks)]

        texts, ids, metas = [], [], []
        oh = getattr(j, "origin_hash", "") or ""
        fn = getattr(j, "filename", "") or ""
        kb = getattr(j, "kb", "default") or "default"
        for i, c in enumerate(chunks):
            if isinstance(c, str):
                txt = c; meta = {}
            else:
                txt = c.get("text") or c.get("content") or c.get("page_content") or ""
                meta = dict(c.get("metadata") or {})
                # [IMG_FIX] 同上
                _imgs = c.get("images")
                if _imgs:
                    import json as _j
                    meta["__images_json__"] = _j.dumps(_imgs, ensure_ascii=False)
            cid = None
            if isinstance(c, dict):
                for k in ("chunk_id", "id", "_id", "uid"):
                    if c.get(k): cid = str(c[k]); break
            if not cid: cid = job_id + "_chunk_" + str(i)
            if oh: meta.setdefault("origin_hash", oh)
            meta.setdefault("job_id", job_id)
            meta.setdefault("filename", fn)
            meta.setdefault("kb", kb)
            texts.append(txt); ids.append(cid); metas.append(meta)

        # [PHASE] 进入"生成向量"
        try:
            if hasattr(worker.registry, "update_progress"):
                worker.registry.update_progress(job_id, {
                    "phase": "embedding", "current": 0,
                    "total": len(texts), "percent": 0.0,
                    "message": f"生成向量 0/{len(texts)}",
                })
        except Exception:
            pass

        embeddings = None
        try:
            from backend.api.rag.ingest_runtime import get_ingest_runtime
            ef = getattr(get_ingest_runtime(), "embed_fn", None)
            if ef is not None and hasattr(ef, "warmup"):
                logger.info("[approve] 预热 Ollama 模型...")
                ef.warmup()
            if callable(ef):
                # [BATCH_EMBED] 分批 + 3 次重试，避免 Ollama 超时
                import time as _t
                _BATCH = int(os.environ.get("RAG_EMBED_BATCH", "8"))
                _RETRY = 3
                embeddings = []
                for _i in range(0, len(texts), _BATCH):
                    _chunk = texts[_i:_i + _BATCH]
                    _last_err = None
                    for _try in range(_RETRY):
                        try:
                            embeddings.extend(ef(_chunk))
                            # [PROGRESS_PUSH] 每批更新前端进度
                            try:
                                _done_n = len(embeddings)
                                _total_n = len(texts)
                                if hasattr(worker.registry, 'update_progress'):
                                    worker.registry.update_progress(job_id, {
                                        'phase': 'embedding',
                                        'current': _done_n,
                                        'total': _total_n,
                                        'percent': _done_n * 100.0 / max(1, _total_n),
                                        'message': f'生成向量 {_done_n}/{_total_n}',
                                    })
                            except Exception:
                                pass
                            _last_err = None
                            break
                        except Exception as _e:
                            _last_err = _e
                            if _try < _RETRY - 1:
                                _t.sleep(1.0 * (_try + 1))
                    if _last_err is not None:
                        raise _last_err
        except Exception as e:
            logger.warning("[approve] embed_fn 失败: %r", e)
        if embeddings is None:
            result["error"] = "embed_fn 无法生成向量"; _recover(); return result

        from backend.storage.vector_backend import get_vector_store
        from backend.storage.vector_config import VectorConfig
        vs = get_vector_store(VectorConfig())

        def _count():
            try:
                col = getattr(vs, "collection", None)
                if col is not None: return col.count()
            except Exception: pass
            return None

        before = _count(); inserted = 0; via = "?"

        col = getattr(vs, "collection", None)
        if col is not None and hasattr(col, "add"):
            try:
                col.add(ids=ids, documents=texts, metadatas=metas, embeddings=embeddings)
                inserted = len(texts); via = "collection.add"
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    inserted = len(texts); via = "collection.add(exists)"
                else: logger.warning("[approve] collection.add: %r", e)

        if inserted == 0:
            try:
                vs.add_documents(documents=texts, ids=ids, metadata=metas, embeddings=embeddings)
                inserted = len(texts); via = "add_documents"
            except Exception as e:
                logger.warning("[approve] add_documents: %r", e)

        after = _count()
        if inserted == 0 and before is not None and after is not None and after > before:
            inserted = after - before; via = "count-delta-recovered"

        _done = getattr(JS, "DONE", None)
        ferr = None
        try:
            worker.registry.finish(job_id, status=_done, chunks_indexed=inserted, error="")
        except Exception as fe:
            ferr = fe

        j2 = worker.registry.get(job_id)
        s2 = getattr(j2.status, "name", str(j2.status)).lower() if j2 else "?"
        result["status"] = s2
        if s2 == "done":
            result.update({"approved": True, "status": "done", "via": via,
                "chunks_indexed": inserted, "count_before": before, "count_after": after})
            if ferr: result["finish_warn"] = str(ferr)[:120]
            return result
        result["error"] = "未完成: inserted=" + str(inserted) + " before=" + str(before) + " after=" + str(after)
        return result

    except Exception as e:
        traceback.print_exc()
        result["error"] = type(e).__name__ + ": " + str(e)[:200]
        _recover()
        return result


def cancel_job_safe(worker: Any, job_id: str) -> Dict[str, Any]:
    """取消 job：兼容 pending_review"""
    from backend.rag.ingest.jobs.registry import JobStatus as JS
    if worker.cancel(job_id):
        return {"cancelled": True, "job_id": job_id, "via": "flag"}
    j = worker.registry.get(job_id)
    if j is None:
        return {"cancelled": False, "job_id": job_id, "error": "not found"}
    cur = getattr(j.status, "name", str(j.status)).lower()
    if cur in ("done", "failed", "cancelled", "rejected"):
        return {"cancelled": False, "job_id": job_id, "reason": "terminal: " + cur}
    st = getattr(JS, "CANCELLED", None)
    worker.registry.finish(job_id, status=st, error="用户取消")
    return {"cancelled": True, "job_id": job_id, "via": "finish"}