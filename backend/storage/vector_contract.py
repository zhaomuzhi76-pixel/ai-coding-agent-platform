"""向量存储统一契约层（工业级后端无关）。
职责：
  - 定义统一操作：list_all / get_by_ids / get_by_where / query / delete / update_metadata / count
  - 检测后端能力，缺失的做兼容适配
  - 让任何后端（Chroma / Lite / Qdrant / 未来）都能被同一套代码访问
不实现存储（各后端 store 管）、不做业务（router 管）。
环境变量：
  RAG_VECTOR_BACKEND=lite|chroma|qdrant
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_store() -> Any:
    """拿当前后端 store（后端无关入口）。"""
    from backend.storage.vector_backend import get_vector_store
    from backend.storage.vector_config import VectorConfig
    return get_vector_store(VectorConfig())


def _inner(res: Any) -> Dict[str, list]:
    """统一“单查询”格式：{"ids":[...], "metadatas":[...], "documents":[...]}"""
    if not isinstance(res, dict):
        return {"ids": [], "metadatas": [], "documents": [], "embeddings": []}
    # 有些后端返回 [[...]] 嵌套（search），有些返回 [...]
    def _flat(v: Any) -> list:
        if isinstance(v, list) and v and isinstance(v[0], list):
            return list(v[0])
        return list(v or [])
    return {
        "ids": _flat(res.get("ids")),
        "metadatas": _flat(res.get("metadatas")),
        "documents": _flat(res.get("documents")),
        "embeddings": _flat(res.get("embeddings")),
    }


def list_all(store: Any, include: Optional[List[str]] = None) -> Dict[str, list]:
    """列出所有向量（后端无关）。
    - Chroma: store.collection.get(include=...)
    - Lite: store.get(include=...) 已支持
    - Qdrant: store.get(ids=None) 或 遍历
    """
    include = include or ["metadatas"]
    # 优先原生 get()
    try:
        r = store.get(include=include)
        return _inner(r)
    except TypeError:
        pass
    # 兜底：遍历 collection
    coll = getattr(store, "collection", store)
    try:
        r = coll.get(include=include)
        return _inner(r)
    except Exception as e:
        logger.warning("[vector-contract] list_all 失败: %r", e)
        return {"ids": [], "metadatas": [], "documents": [], "embeddings": []}


def get_by_ids(store: Any, ids: List[str],
               include: Optional[List[str]] = None) -> Dict[str, list]:
    include = include or ["metadatas", "documents"]
    try:
        r = store.get(ids=ids, include=include)
        return _inner(r)
    except TypeError:
        r = store.get(ids=ids)
        return _inner(r)


def get_by_where(store: Any, where: Dict[str, Any],
                 include: Optional[List[str]] = None) -> Dict[str, list]:
    """按 metadata 字段查。Lite 支持，Chroma 用 .get(where=) 也支持。"""
    include = include or []
    try:
        r = store.get(where=where, include=include)
        return _inner(r)
    except TypeError:
        # 后端不支持 where → 拉全量再过滤
        all_r = list_all(store, ["metadatas"])
        hits = {"ids": [], "metadatas": [], "documents": [], "embeddings": []}
        for i, m in enumerate(all_r.get("metadatas", [])):
            ok = all(str((m or {}).get(k, "")) == str(v) for k, v in where.items())
            if ok:
                hits["ids"].append(all_r["ids"][i])
                hits["metadatas"].append(m)
        return hits


def query(store: Any, *, query_embeddings: List[List[float]],
          n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, list]:
    """向量相似检索（统一契约）。
    - Chroma: coll.query(query_embeddings=..., n_results=...)
    - Lite:   store.search(query_embeddings, limit=..., where=...)
    - Qdrant: store.search(query_embeddings, limit=...)
    返回 Chroma 兼容格式：{"ids": [[...]], "documents": [[...]],
                           "metadatas": [[...]], "distances": [[...]]}
    """
    # 1) 优先试 search（Lite/Qdrant 均有）
    if hasattr(store, "search"):
        try:
            r = store.search(query_embeddings, limit=n_results, where=where)
            # search 返回已是 Chroma 格式（[[...]] 嵌套）
            if isinstance(r, dict):
                return r
        except Exception as e:
            logger.warning("[vector-contract] search 失败，回退 query: %r", e)
    # 2) 退到 chromadb 原生
    coll = getattr(store, "collection", store)
    kw: Dict[str, Any] = {
        "query_embeddings": query_embeddings,
        "n_results": n_results,
    }
    if where:
        kw["where"] = where
    return coll.query(**kw)


def delete(store: Any, ids: List[str]) -> Dict[str, Any]:
    if not ids:
        return {"deleted": 0}
    try:
        return store.delete(ids) or {"deleted": len(ids)}
    except Exception as e:
        logger.warning("[vector-contract] delete 失败: %r", e)
        return {"deleted": 0, "error": str(e)}


def update_metadata(store: Any, ids: List[str],
                    metadatas: List[dict]) -> int:
    """更新 metadata。Chroma 原生，Lite 需要补齐。返回更新数。"""
    if not ids:
        return 0
    # 1) Chroma
    coll = getattr(store, "collection", store)
    if hasattr(coll, "update"):
        try:
            coll.update(ids=ids, metadatas=metadatas)
            return len(ids)
        except Exception as e:
            logger.warning("[vector-contract] update 失败: %r", e)
    return 0


def count(store: Any) -> int:
    try:
        return int(store.count())
    except Exception:
        return 0


__all__ = ["get_store", "list_all", "get_by_ids", "get_by_where",
           "query", "delete", "update_metadata", "count"]
