"""RAG 向量库共享 helper。

职责：
  - _safe_images：从 metadata 解 images（无图返回 []）
  - _collection：取 Chroma/Lite collection
  - _store：取 vector store 单例
  - _delete_ids：批量删
不做：
  - 不做业务逻辑（各 router 管）
  - 不写 HTTP 端点
"""
from __future__ import annotations
import json
from typing import List


def _safe_images(m):
    """从 metadata 解 images（无图返回 []）。"""
    raw = (m or {}).get("__images_json__")
    if not raw:
        return []
    try:
        out = json.loads(raw) if isinstance(raw, str) else list(raw)
        return out if isinstance(out, list) else []
    except Exception:
        return []


def _collection():
    """取向量集合（后端无关）。"""
    from backend.storage.vector_backend import get_vector_store
    from backend.storage.vector_config import VectorConfig
    store = get_vector_store(VectorConfig())
    return getattr(store, "collection", None) or store


def _store():
    """取向量 store（供 query 用）。"""
    from backend.storage.vector_backend import get_vector_store
    from backend.storage.vector_config import VectorConfig
    return get_vector_store(VectorConfig())


def _delete_ids(ids: List[str]) -> int:
    """批量删。返回删除数。"""
    if not ids:
        return 0
    try:
        coll = _collection()
        coll.delete(ids=list(ids))
        return len(ids)
    except Exception:
        return 0


__all__ = ["_safe_images", "_collection", "_store", "_delete_ids"]
