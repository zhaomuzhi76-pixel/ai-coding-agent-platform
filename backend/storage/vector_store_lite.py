"""轻量向量库。按 collection 分库 + 维度自适应，避免维度混用崩溃。"""
from __future__ import annotations
import json, os, sqlite3, threading
from typing import Any, List, Optional
import numpy as np


class LiteVectorStore:
    VERSION = "1.1"

    def __init__(self, config) -> None:
        self.config = config
        os.makedirs(config.path, exist_ok=True)
        # 每个 collection 独立 db，避免维度/元数据混用
        safe = "".join(c if c.isalnum() or c in "._-" else "_"
                       for c in config.collection_name)
        self._db_path = os.path.join(config.path, f"lite_{safe}.db")
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS docs (
                id TEXT PRIMARY KEY,
                text TEXT,
                metadata TEXT,
                embedding BLOB,
                dim INTEGER
            )
        """)
        self._conn.commit()
        self._lock = threading.Lock()
        self._cache = None

    @property
    def collection(self): return self
    @property
    def collection_name(self): return self.config.collection_name
    @property
    def embedding_model(self): return self.config.embedding_model

    def _load_cache(self):
        if self._cache is not None:
            return self._cache
        cur = self._conn.execute(
            "SELECT id, text, metadata, embedding, dim FROM docs")
        # 按维度分组：只用最大维度组（同模型写入）
        by_dim = {}
        for id_, text, meta_str, blob, dim in cur.fetchall():
            if blob is None or dim is None:
                continue
            try: meta = json.loads(meta_str or "{}")
            except Exception: meta = {}
            vec = np.frombuffer(blob, dtype="<f4")
            by_dim.setdefault(dim, []).append((id_, text, meta, vec))
        if not by_dim:
            self._cache = ([], [], [], np.zeros((0, 0), dtype=np.float32))
            return self._cache
        # 取最大的维度组（最可能的当前模型）
        best_dim = max(by_dim.keys(), key=lambda d: len(by_dim[d]))
        items = by_dim[best_dim]
        ids = [x[0] for x in items]
        texts = [x[1] for x in items]
        metas = [x[2] for x in items]
        vecs = [x[3] for x in items]
        m = np.stack(vecs).astype(np.float32)
        norms = np.linalg.norm(m, axis=1, keepdims=True) + 1e-8
        self._cache = (ids, texts, metas, m / norms)
        return self._cache

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]

    def count_by_dim(self) -> dict:
        cur = self._conn.execute(
            "SELECT dim, COUNT(*) FROM docs GROUP BY dim")
        return {d: n for d, n in cur.fetchall()}

    def add_documents(self, documents, ids, metadata=None,
                      embeddings=None, **_kw):
        if embeddings is None:
            raise ValueError("embeddings required")
        if metadata is None:
            metadata = [{} for _ in ids]
        with self._lock:
            for i, id_ in enumerate(ids):
                vec = np.asarray(embeddings[i], dtype=np.float32)
                self._conn.execute(
                    "INSERT OR REPLACE INTO docs "
                    "(id, text, metadata, embedding, dim) VALUES (?,?,?,?,?)",
                    (id_, documents[i],
                     json.dumps(metadata[i], ensure_ascii=False),
                     vec.tobytes(), int(vec.shape[0])))
            self._conn.commit()
            self._cache = None
        return {"success": True, "count": len(ids), "version": self.VERSION}

    def upsert_documents(self, documents, ids, metadata=None,
                         embeddings=None, **_kw):
        return self.add_documents(documents, ids, metadata, embeddings)

    def search(self, query_embeddings, limit=5, where=None):
        ids, texts, metas, matrix = self._load_cache()
        empty = {"ids": [[]], "documents": [[]],
                 "metadatas": [[]], "distances": [[]]}
        if not ids:
            return empty
        q = np.asarray(query_embeddings[0], dtype=np.float32)
        if q.shape[0] != matrix.shape[1]:
            return empty  # 维度不匹配：空返回而非崩溃
        q = q / (np.linalg.norm(q) + 1e-8)
        scores = matrix @ q
        if where:
            # [FIX] where 过滤：彻底排除不匹配项，不能只降分
            mask = np.ones(len(ids), dtype=bool)
            for k, v in where.items():
                mask &= np.array(
                    [str(m.get(k, "")) == str(v) for m in metas])
            valid_idx = np.where(mask)[0]
            if len(valid_idx) == 0:
                return empty
            sub_scores = scores[valid_idx]
            sub_top = np.argsort(-sub_scores)[:limit]
            top = valid_idx[sub_top]
        else:
            top = np.argsort(-scores)[:limit]
        return {
            "ids": [[ids[i] for i in top]],
            "documents": [[texts[i] for i in top]],
            "metadatas": [[metas[i] for i in top]],
            "distances": [[float(1.0 - scores[i]) for i in top]],
        }

    def get(self, ids=None, include=None, where=None,
            limit=None, offset=0, **_kw):
        """兼容 Chroma collection.get(ids=, include=, where=, limit=, offset=)。"""
        params = []
        if ids:
            ph = ",".join("?" * len(ids))
            sql = f"SELECT id, text, metadata FROM docs WHERE id IN ({ph})"
            params = list(ids)
        else:
            sql = "SELECT id, text, metadata FROM docs"
            conds = []
            if where:
                for k, v in where.items():
                    conds.append("metadata LIKE ?")
                    params.append(f'%"{k}": "{v}"%')
            if conds:
                sql += " WHERE " + " AND ".join(conds)
            if limit:
                sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = self._conn.execute(sql, params).fetchall()
        return {"ids": [r[0] for r in rows],
                "documents": [r[1] for r in rows],
                "metadatas": [json.loads(r[2] or "{}") for r in rows]}

    def delete(self, ids):
        if not ids: return {"success": True, "deleted": 0}
        with self._lock:
            ph = ",".join("?" * len(ids))
            cur = self._conn.execute(
                f"DELETE FROM docs WHERE id IN ({ph})", ids)
            self._conn.commit()
            self._cache = None
            return {"success": True, "deleted": cur.rowcount}

    # ─── [CONTRACT] 对齐 Chroma API（后端无关契约）───
    def query(self, query_embeddings, n_results=5, where=None, **kw):
        """Chroma 兼容：向量检索。内部委托 self.search。"""
        return self.search(query_embeddings, limit=n_results, where=where)

    def update(self, ids, metadatas=None, **kw):
        """Chroma 兼容：更新 metadata。"""
        if not ids or metadatas is None:
            return {"updated": 0}
        with self._lock:
            n = 0
            for i, id_ in enumerate(ids):
                m = metadatas[i] if i < len(metadatas) else {}
                cur = self._conn.execute(
                    "SELECT metadata FROM docs WHERE id=?", (id_,))
                row = cur.fetchone()
                if row is None:
                    continue
                import json as _json
                try:
                    old = _json.loads(row[0] or "{}")
                except Exception:
                    old = {}
                old.update(m or {})
                self._conn.execute(
                    "UPDATE docs SET metadata=? WHERE id=?",
                    (_json.dumps(old, ensure_ascii=False), id_))
                n += 1
            self._conn.commit()
            self._cache = None
        return {"updated": n}

    def reload(self): self._cache = None
    def health(self): return {"ok": True, "backend": "lite",
                              "count": self.count(),
                              "by_dim": self.count_by_dim()}
    def dump(self): return {"name": "LiteVectorStore",
                            "version": self.VERSION,
                            "db": self._db_path,
                            "count": self.count()}


__all__ = ["LiteVectorStore"]
