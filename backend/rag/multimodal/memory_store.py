"""内存向量存储（工业级，Chroma API 子集）。

职责：upsert / query / count。可选 jsonl 持久化。
不做：不编码、不改语义。
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def _as_batch(qe):
    """归一 query 输入：list[float] / list[list[float]] / tensor → list[list[float]]。"""
    if qe is None:
        return []
    if hasattr(qe, "tolist"):
        qe = qe.tolist()
    if not isinstance(qe, (list, tuple)):
        return [[qe]]
    if not qe:
        return []
    first = qe[0]
    if isinstance(first, (list, tuple)):
        return [list(v) for v in qe]
    if hasattr(first, "tolist"):
        return [qe[0].tolist()] if len(qe) == 1 else [v.tolist() for v in qe]
    return [list(qe)]


def _match_where(meta, where):
    """最小 where 匹配：dict 精确 or {'$in': [...]} / {'$eq': v}。"""
    if not where:
        return True
    for k, cond in where.items():
        val = (meta or {}).get(k)
        if isinstance(cond, dict):
            if "$in" in cond and val not in cond["$in"]:
                return False
            if "$eq" in cond and val != cond["$eq"]:
                return False
        else:
            if val != cond:
                return False
    return True


def _cos(a: Sequence[float], b: Sequence[float]) -> float:
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / math.sqrt(na * nb)


class MemoryVectorStore:
    def __init__(self, name: str = "mm", persist_path: Optional[str] = None):
        self.name = name
        self._ids: List[str] = []
        self._texts: List[str] = []
        self._metas: List[Dict[str, Any]] = []
        self._vecs: List[List[float]] = []
        self._persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            self._load()

    def _load(self):
        try:
            with open(self._persist_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    self._ids.append(rec["id"])
                    self._texts.append(rec.get("text", ""))
                    self._metas.append(rec.get("meta", {}))
                    self._vecs.append(rec.get("vec", []))
        except Exception:
            pass

    def _save_append(self, rec: Dict[str, Any]):
        if not self._persist_path:
            return
        Path(self._persist_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._persist_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def upsert(self, image_id: str, vec, **meta) -> None:
        """单条图片 upsert（image_index/indexer 用）。

        签名：upsert(image_id, vec, origin_hash=..., mime=..., width=...,
                     height=..., text=..., metadata={...})
        所有 kwargs 并入 metadata；原 metadata 字段展开到顶层。
        """
        nested = meta.pop("metadata", None)
        base = dict(meta)
        if isinstance(nested, dict):
            base.update(nested)
        text = base.pop("text", "")
        rec = {"id": image_id, "text": text,
               "meta": base, "vec": list(vec)}
        self._ids.append(image_id)
        self._texts.append(text)
        self._metas.append(base)
        self._vecs.append(rec["vec"])
        self._save_append(rec)

    def upsert_documents(self, documents=None, ids=None,
                         metadata=None, embeddings=None, **kw):
        """批量文本 upsert（multimodal/indexer 用）。

        位置参数顺序：(documents, ids, metadata=None, embeddings=None)
        兼容旧 keyword: metadatas= / texts=
        """
        if metadata is None:
            metadata = kw.pop("metadatas", None) or []
        docs = documents if documents is not None else (kw.get("texts") or [])
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(docs))]
        for i, cid in enumerate(ids):
            vec = embeddings[i] if embeddings else []
            rec = {"id": cid,
                   "text": docs[i] if i < len(docs) else "",
                   "meta": dict(metadata[i]) if i < len(metadata) else {},
                   "vec": list(vec)}
            self._ids.append(cid)
            self._texts.append(rec["text"])
            self._metas.append(rec["meta"])
            self._vecs.append(rec["vec"])
            self._save_append(rec)

    # ---- 原图存取（image_index/indexer 用） ----
    def put_file(self, path_or_bytes, **kwargs) -> dict:
        """存原图字节；返回 {origin_hash, size, mime}。幂等。"""
        import hashlib
        if isinstance(path_or_bytes, (bytes, bytearray, memoryview)):
            data = bytes(path_or_bytes)
            mime = kwargs.get("mime", "image/png")
        else:
            p = str(path_or_bytes)
            with open(p, "rb") as f:
                data = f.read()
            ext = p.rsplit(".", 1)[-1].lower() if "." in p else "png"
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        h = hashlib.sha1(data).hexdigest()[:20]
        if not hasattr(self, "_files"):
            self._files = {}
        self._files[h] = data
        return {"hash": h, "origin_hash": h, "size": len(data), "mime": mime}

    def get_file(self, key):
        return getattr(self, "_files", {}).get(key)

    def has_file(self, key) -> bool:
        return key in getattr(self, "_files", {})

    def count(self) -> int:
        return len(self._ids)

    def search(self, query_embeddings=None, top_k: int = 10,
               where=None, **kw):
        """image_index 契约：返回 list[(id, score, meta)]。

        与 query() 的区别：
          query()  → dict（Chroma 风格，multimodal/service 用）
          search() → list[tuple]（image_index/retriever 用）
        """
        batches = _as_batch(query_embeddings)
        q = batches[0] if batches else []
        scored = []
        for i, v in enumerate(self._vecs):
            if not v:
                continue
            if not _match_where(self._metas[i], where):
                continue
            scored.append((_cos(q, v), i))
        scored.sort(reverse=True)
        top = scored[:max(0, int(top_k))]
        return [(self._ids[i], s, self._metas[i]) for s, i in top]

    def query(self, query_embeddings=None, n_results: int = 10,
              where=None, **kw):
        """统一 query：接受单向量或批量向量；支持 where 过滤。

        返回 dict：{ids, documents, metadatas, distances}，均为 batch list。
        """
        batches = _as_batch(query_embeddings)
        q = batches[0] if batches else []
        scored = []
        for i, v in enumerate(self._vecs):
            if not v:
                continue
            if not _match_where(self._metas[i], where):
                continue
            scored.append((_cos(q, v), i))
        scored.sort(reverse=True)
        top = scored[:max(0, int(n_results))]
        return {
            "ids": [[self._ids[i] for _, i in top]],
            "documents": [[self._texts[i] for _, i in top]],
            "metadatas": [[self._metas[i] for _, i in top]],
            "distances": [[1.0 - s for s, _ in top]],
        }

def make_store(name: str = "mm", persist_path: Optional[str] = None):
    return MemoryVectorStore(name=name, persist_path=persist_path)


__all__ = ["MemoryVectorStore", "make_store"]
