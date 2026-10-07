"""图片向量存储。职责：独立 Chroma collection 的增删查（image_id → 向量）。
不编码（clip_engine 管）、不做语义检索编排（retriever 管）、不落盘原件（origin_store 管）。
用独立 collection（agent_image_index），与主库物理隔离，避免维度冲突。
线程安全。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import os
from threading import RLock
from typing import Any, Mapping, Optional, Sequence

import chromadb

COLLECTION_NAME = "agent_image_index"
DEFAULT_PATH = os.path.expanduser("~/.cache/agent_image_index")


class ImageVectorStore:
    def __init__(self, *, path: Optional[str] = None,
                 collection: str = COLLECTION_NAME) -> None:
        self._path = path or os.getenv("IMAGE_INDEX_PATH", DEFAULT_PATH)
        self._name = collection
        self._client = None
        self._col = None
        self._lock = RLock()

    # ---------- 懒加载 ----------
    def _ensure(self):
        if self._col is not None:
            return self._col
        with self._lock:
            if self._col is not None:
                return self._col
            os.makedirs(self._path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self._path)
            self._col = self._client.get_or_create_collection(
                name=self._name,
                metadata={"hnsw:space": "cosine"})  # 余弦距离
            return self._col

    # ---------- 写入 ----------
    def upsert(self, image_id: str, vector: Sequence[float], *,
               origin_hash: str = "", mime: str = "",
               width: int = 0, height: int = 0, text: str = "",
               metadata: Optional[Mapping[str, Any]] = None) -> None:
        if not image_id:
            raise ValueError("image_id required")
        v = [float(x) for x in vector]
        if not v:
            raise ValueError("vector must not be empty")
        meta: dict = {
            "origin_hash": str(origin_hash or ""),
            "mime": str(mime or ""),
            "width": int(width),
            "height": int(height),
            "text": str(text or ""),
        }
        if metadata:
            for k, val in metadata.items():
                if isinstance(val, (str, int, float, bool)):
                    meta[str(k)] = val
        col = self._ensure()
        with self._lock:
            col.upsert(ids=[image_id], embeddings=[v], metadatas=[meta])

    def upsert_many(self, items: Sequence[Mapping[str, Any]]) -> int:
        """items: [{"image_id","vector","origin_hash",...}, ...]"""
        col = self._ensure()
        ids: list = []
        embs: list = []
        metas: list = []
        for it in items:
            iid = str(it.get("image_id", ""))
            if not iid: continue
            vec = it.get("vector")
            if not vec: continue
            ids.append(iid)
            embs.append([float(x) for x in vec])
            metas.append({
                "origin_hash": str(it.get("origin_hash", "")),
                "mime": str(it.get("mime", "")),
                "width": int(it.get("width", 0)),
                "height": int(it.get("height", 0)),
                "text": str(it.get("text", "")),
            })
        if not ids:
            return 0
        with self._lock:
            col.upsert(ids=ids, embeddings=embs, metadatas=metas)
        return len(ids)

    def delete(self, image_id: str) -> bool:
        if not image_id: return False
        col = self._ensure()
        with self._lock:
            try:
                col.delete(ids=[image_id])
                return True
            except Exception:
                return False

    def clear(self) -> None:
        col = self._ensure()
        with self._lock:
            try:
                self._client.delete_collection(self._name)
            except Exception as e:
                swallow("rag.image_index.store:109", e)
            self._col = None

    # ---------- 查询 ----------
    def count(self) -> int:
        try:
            return int(self._ensure().count())
        except Exception:
            return 0

    def search(self, vector: Sequence[float], *, top_k: int = 10,
               where: Optional[Mapping[str, Any]] = None) -> list:
        """返回 [(image_id, similarity, metadata), ...] similarity 0..1。"""
        if top_k <= 0:
            raise ValueError("top_k must be > 0")
        v = [float(x) for x in vector]
        if not v:
            raise ValueError("vector must not be empty")
        col = self._ensure()
        try:
            data = col.query(
                query_embeddings=[v], n_results=top_k,
                where=dict(where) if where else None,
                include=["metadatas", "distances"])
        except Exception:
            return []
        ids = (data.get("ids") or [[]])[0]
        dists = (data.get("distances") or [[]])[0]
        metas = (data.get("metadatas") or [[]])[0]
        out: list = []
        for i, iid in enumerate(ids):
            d = float(dists[i]) if i < len(dists) else 1.0
            sim = 1.0 - d if d <= 1.0 else 0.0
            meta = dict(metas[i]) if i < len(metas) and metas[i] else {}
            out.append((str(iid), max(0.0, min(1.0, sim)), meta))
        return out

    def get(self, image_id: str) -> Optional[dict]:
        """按 image_id 取元数据。不返回向量（numpy 兼容复杂，避免过度）。"""
        col = self._ensure()
        try:
            data = col.get(ids=[image_id], include=["metadatas"])
            ids = data.get("ids")
            if ids is None or len(ids) == 0:
                return None
            metas = data.get("metadatas")
            meta = dict(metas[0]) if (metas is not None
                                       and len(metas) > 0 and metas[0]) else {}
            return {
                "image_id": str(ids[0]),
                "metadata": meta,
                "vector": (),
            }
        except Exception:
            return None


_DEFAULT: Optional[ImageVectorStore] = None


def get_default_image_store() -> ImageVectorStore:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = ImageVectorStore()
    return _DEFAULT


def set_default_image_store(s: Optional[ImageVectorStore]) -> None:
    global _DEFAULT
    _DEFAULT = s


__all__ = ["ImageVectorStore", "get_default_image_store",
           "set_default_image_store", "COLLECTION_NAME", "DEFAULT_PATH"]
