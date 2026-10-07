"""Embed 阶段：单调度，3 线程并发调 embed_fn。
  queue.dequeue('embed') → 读 draft → 分批并发 embed
  → 每批入 'vecwrite' 队列（base64 编码向量）
"""
from __future__ import annotations
import base64
import logging
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def _vecs_to_b64(vecs: List[List[float]]) -> str:
    """float32 小端序列化 → base64（紧凑传输）。"""
    buf = bytearray()
    for v in vecs:
        buf.extend(struct.pack("<" + "f" * len(v), *v))
    return base64.b64encode(bytes(buf)).decode("ascii")


def _b64_to_vecs(b64: str, dim: int) -> List[List[float]]:
    raw = base64.b64decode(b64)
    n = len(raw) // (4 * dim)
    out = []
    off = 0
    for _ in range(n):
        v = list(struct.unpack_from("<" + "f" * dim, raw, off))
        out.append(v)
        off += 4 * dim
    return out


class EmbedStage:
    def __init__(self, queue: Any, budget: Any,
                 embed_fn: Any, draft_store: Any, *,
                 workers: int = 3, batch_size: int = 16,
                 poll_interval: float = 1.0) -> None:
        self._q = queue
        self._budget = budget
        self._embed = embed_fn
        self._drafts = draft_store
        self._workers = max(1, int(workers))
        self._bs = max(1, int(batch_size))
        self._poll = poll_interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        last_err = None
        for attempt in range(3):
            try:
                return self._embed(texts)
            except Exception as e:
                last_err = e
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"embed batch failed: {last_err!r}")

    def run_once(self) -> bool:
        item = self._q.dequeue("embed")
        if not item:
            return False
        rid = item["id"]
        job_id = item["job_id"]
        pl = item["payload"]
        draft_path = pl.get("draft_path", "")
        if not draft_path:
            self._q.fail(rid, "draft_path missing")
            return True

        # 限制实际并发到 GPU 预算内
        workers = min(self._workers, self._budget.max_embed_workers())
        self._budget.acquire_embed()
        try:
            chunks = self._drafts.read(job_id)
            if not chunks:
                self._q.fail(rid, "draft empty")
                return True
            texts = [c.text for c in chunks]
            ids = [c.chunk_id for c in chunks]
            metas = [dict(c.metadata) for c in chunks]
            total = len(texts)
            dim_holder = {"dim": 0}

            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = []
                for i in range(0, total, self._bs):
                    batch = texts[i:i + self._bs]
                    futures.append((i, ex.submit(self._embed_batch, batch)))
                for offset, fut in futures:
                    vecs = fut.result()
                    dim = len(vecs[0]) if vecs else 0
                    if dim_holder["dim"] == 0:
                        dim_holder["dim"] = dim
                    b64 = _vecs_to_b64(vecs)
                    self._q.enqueue(
                        job_id, "vecwrite",
                        payload={
                            "ids": ids[offset:offset + len(vecs)],
                            "documents": texts[offset:offset + len(vecs)],
                            "metadata": metas[offset:offset + len(vecs)],
                            "vectors_b64": b64,
                            "dim": dim,
                            "total": total,
                            "batch_end": offset + len(vecs),
                        },
                        priority=0)
            self._q.complete(rid)
            print(f"[embed-stage] job={job_id} ✅ total={total} workers={workers}",
                  flush=True)
        except Exception as e:
            logger.error("[embed-stage] job=%s 失败: %r", job_id, e)
            self._q.fail(rid, f"{type(e).__name__}: {e}")
        finally:
            self._budget.release_embed()
        return True

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if not self.run_once():
                    self._stop.wait(self._poll)
            except Exception as e:
                logger.error("[embed-stage] loop 异常: %r", e)
                time.sleep(1.0)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop,
                                        name="pipeline-embed", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)


__all__ = ["EmbedStage", "_vecs_to_b64", "_b64_to_vecs"]
