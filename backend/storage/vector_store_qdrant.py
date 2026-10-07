"""Qdrant 存储实现。职责：100% 对齐 VectorStore 接口（11 方法）。
不选后端（vector_backend 管）、不做 embed（外部 EmbeddingService 管）。
辅助函数在 qdrant_helpers.py。维度懒推断：首次 upsert 时按 embeddings 长度建表。
"""
from __future__ import annotations
from typing import Any, Optional

from backend.storage.qdrant_helpers import (
    build_client, ensure_collection, probe_dim,
    to_qdrant_filter, to_qdrant_id)
from backend.storage.vector_config import VectorConfig


class QdrantStore:
    VERSION = "1.0"

    def __init__(self, config: Optional[VectorConfig] = None) -> None:
        self.config = config or VectorConfig()
        self._client = None
        self._col = self.config.collection_name
        self._dim: Optional[int] = None

    @property
    def collection_name(self) -> str:
        return self._col

    @property
    def embedding_model(self) -> str:
        return self.config.embedding_model

    @property
    def client(self):
        return self._ensure()

    # ---------- 懒加载 ----------
    def _ensure(self):
        if self._client is not None:
            return self._client
        self._client = build_client(self.config.qdrant_url,
                                     self.config.qdrant_api_key or "")
        try:
            self._client.get_collections()
        except Exception as e:
            raise RuntimeError(
                f"Qdrant 连接失败 ({self.config.qdrant_url}): "
                f"{type(e).__name__}: {e}") from e
        self._dim = probe_dim(self._client, self._col)
        return self._client

    def reload(self) -> None:
        self._client = None
        self._dim = None

    # ---------- 写入 ----------
    def add_documents(self, documents, ids, metadata=None,
                      embeddings=None) -> dict:
        return self.upsert_documents(documents, ids, metadata, embeddings)

    def upsert_documents(self, documents, ids, metadata=None,
                         embeddings=None) -> dict:
        if embeddings is None:
            raise ValueError(
                "embeddings required, use external EmbeddingService")
        if not documents or not ids:
            return {"upserted": 0}
        if len(documents) != len(ids) or len(ids) != len(embeddings):
            raise ValueError("documents/ids/embeddings 长度不一致")
        dim = len(embeddings[0])
        self._dim = ensure_collection(self._ensure(), self._col,
                                       dim, self._dim)
        try:
            from qdrant_client.models import PointStruct
        except ImportError as e:
            raise RuntimeError("qdrant-client 缺 models") from e
        metas = metadata or [None] * len(ids)
        points = []
        for i, pid in enumerate(ids):
            payload = {"doc_id": str(pid), "document": str(documents[i])}
            m = metas[i] if i < len(metas) else None
            if m:
                for k, v in m.items():
                    if isinstance(v, (str, int, float, bool)):
                        payload[str(k)] = v
            points.append(PointStruct(
                id=to_qdrant_id(pid),
                vector=[float(x) for x in embeddings[i]],
                payload=payload))
        self._ensure().upsert(collection_name=self._col, points=points,
                               wait=True)
        return {"upserted": len(points)}

    # ---------- 查询 ----------
    def search(self, query_embeddings, limit: int = 5,
               where=None) -> dict:
        if not query_embeddings:
            raise ValueError("query_embeddings required")
        if limit <= 0:
            raise ValueError("limit must be > 0")
        c = self._ensure()
        try:
            c.get_collection(self._col)
        except Exception:
            return {"ids": [[]], "documents": [[]],
                    "metadatas": [[]], "distances": [[]]}
        # qdrant-client >= 1.10 把 search 改名为 query_points
        if hasattr(c, "query_points"):
            r = c.query_points(
                collection_name=self._col,
                query=[float(x) for x in query_embeddings[0]],
                limit=int(limit),
                query_filter=to_qdrant_filter(where))
            hits = r.points
        else:
            hits = c.search(
                collection_name=self._col,
                query_vector=[float(x) for x in query_embeddings[0]],
                limit=int(limit),
                query_filter=to_qdrant_filter(where))
        ids, docs, metas, dists = [], [], [], []
        for h in hits:
            payload = h.payload or {}
            ids.append(str(payload.get("doc_id", h.id)))
            docs.append(str(payload.get("document", "")))
            metas.append({k: v for k, v in payload.items()
                          if k not in ("doc_id", "document")})
            # Qdrant COSINE → 转"距离"对齐 Chroma L2 语义
            dists.append(max(0.0, 1.0 - float(h.score)))
        return {"ids": [ids], "documents": [docs],
                "metadatas": [metas], "distances": [dists]}

    def get(self, ids: list) -> dict:
        if not ids: return {"ids": [], "documents": [], "metadatas": []}
        try:
            pts = self._ensure().retrieve(
                collection_name=self._col,
                ids=[to_qdrant_id(i) for i in ids],
                with_payload=True, with_vectors=False)
        except Exception:
            return {"ids": [], "documents": [], "metadatas": []}
        out_ids, out_docs, out_metas = [], [], []
        for p in pts:
            payload = p.payload or {}
            out_ids.append(str(payload.get("doc_id", p.id)))
            out_docs.append(str(payload.get("document", "")))
            out_metas.append({k: v for k, v in payload.items()
                              if k not in ("doc_id", "document")})
        return {"ids": out_ids, "documents": out_docs,
                "metadatas": out_metas}

    def delete(self, ids: list) -> dict:
        if not ids: return {"deleted": 0}
        try:
            from qdrant_client.models import PointIdsList
        except ImportError:
            return {"deleted": 0}
        try:
            self._ensure().delete(
                collection_name=self._col,
                points_selector=PointIdsList(
                    points=[to_qdrant_id(i) for i in ids]))
            return {"deleted": len(ids)}
        except Exception as e:
            return {"deleted": 0, "error": str(e)}

    def count(self) -> int:
        try:
            info = self._ensure().get_collection(self._col)
            return int(getattr(info, "points_count", 0) or 0)
        except Exception:
            return 0

    def health(self) -> dict:
        try:
            self._ensure().get_collections()
            return {"ok": True, "backend": "qdrant",
                    "url": self.config.qdrant_url,
                    "collection": self._col}
        except Exception as e:
            return {"ok": False, "backend": "qdrant",
                    "error": f"{type(e).__name__}: {e}"}

    def dump(self) -> dict:
        return {"name": "QdrantStore", "version": self.VERSION,
                "collection": self._col, "dim": self._dim,
                "url": self.config.qdrant_url}


__all__ = ["QdrantStore"]
