"""向量写入阶段：单 worker 串行写 SQLite，规避 database is locked。
  queue.dequeue('vecwrite') → base64 解码 → vector_store.add_documents
  → 若全部批完成 → 触发 on_job_done 回调
"""
from __future__ import annotations
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class VecWriteStage:
    def __init__(self, queue: Any, vector_store: Any, *,
                 on_job_done: Optional[Callable[[str], None]] = None,
                 poll_interval: float = 1.0) -> None:
        self._q = queue
        self._vs = vector_store
        self._on_done = on_job_done
        self._poll = poll_interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        # 每个 job 的进度跟踪
        self._progress: Dict[str, Dict[str, int]] = {}
        self._lock = threading.Lock()

    def _bump_progress(self, job_id: str, total: int,
                       written: int) -> bool:
        """返回 True 表示所有批次已完成。"""
        with self._lock:
            st = self._progress.setdefault(
                job_id, {"written": 0, "total": int(total)})
            st["written"] += int(written)
            st["total"] = max(st["total"], int(total))
            done = st["written"] >= st["total"] and st["total"] > 0
            if done:
                self._progress.pop(job_id, None)
            return done

    def run_once(self) -> bool:
        item = self._q.dequeue("vecwrite")
        if not item:
            return False
        rid = item["id"]
        job_id = item["job_id"]
        pl = item["payload"]
        try:
            from backend.rag.ingest.pipeline.stage_embed import _b64_to_vecs
            ids = list(pl.get("ids") or [])
            docs = list(pl.get("documents") or [])
            metas = list(pl.get("metadata") or [])
            dim = int(pl.get("dim") or 0)
            b64 = pl.get("vectors_b64", "")
            total = int(pl.get("total") or len(ids))
            if not ids or len(ids) != len(docs) or len(ids) != len(metas):
                raise ValueError("ids/documents/metadata 长度不一致")
            if dim <= 0 or not b64:
                raise ValueError("vectors_b64 / dim required")
            vecs = _b64_to_vecs(b64, dim)
            if len(vecs) != len(ids):
                raise ValueError(
                    f"向量数 {len(vecs)} != ids 数 {len(ids)}")
            # 打标：写入时标记 pending，最后翻转
            mts = [dict(m, _job_pending=True, _job_id=job_id)
                   for m in metas]
            self._vs.add_documents(documents=docs, ids=ids,
                                   metadata=mts, embeddings=vecs)
            self._q.complete(rid)
            done = self._bump_progress(job_id, total, len(ids))
            print(f"[vecwrite] job={job_id} 写入 {len(ids)} 条 done={done}",
                  flush=True)
            if done and self._on_done:
                try:
                    self._flip_visible(job_id)
                    self._on_done(job_id)
                except Exception as e:
                    logger.error("[vecwrite] on_done 异常: %r", e)
        except Exception as e:
            logger.error("[vecwrite] job=%s 失败: %r", job_id, e)
            self._q.fail(rid, f"{type(e).__name__}: {e}")
        return True

    def _flip_visible(self, job_id: str) -> None:
        """原子可见：把该 job 的 _job_pending 翻为 False。"""
        import json
        try:
            conn = getattr(self._vs, "_conn", None)
            if conn is None:
                return
            cur = conn.execute("SELECT id, metadata FROM docs")
            n = 0
            for _id, _mj in cur.fetchall():
                try:
                    m = json.loads(_mj or "{}")
                except Exception:
                    continue
                if m.get("_job_id") == job_id and m.get("_job_pending"):
                    m["_job_pending"] = False
                    conn.execute(
                        "UPDATE docs SET metadata=? WHERE id=?",
                        (json.dumps(m, ensure_ascii=False), _id))
                    n += 1
            conn.commit()
            if hasattr(self._vs, "_cache"):
                self._vs._cache = None
            print(f"[vecwrite] job={job_id} 翻转 {n} 条为可见", flush=True)
        except Exception as e:
            logger.warning("[vecwrite] 翻转失败: %r", e)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if not self.run_once():
                    self._stop.wait(self._poll)
            except Exception as e:
                logger.error("[vecwrite] loop 异常: %r", e)
                time.sleep(1.0)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop,
                                        name="pipeline-vecwrite",
                                        daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)


__all__ = ["VecWriteStage"]
