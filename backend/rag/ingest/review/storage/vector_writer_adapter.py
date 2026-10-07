"""L2 向量库写入适配器 —— 匹配 VectorStore(VectorConfig) 构造。

约束：VectorConfig.path 强制指向 /dev/shm，避免 chromadb 落盘。
"""
from __future__ import annotations

import importlib
from typing import Any

_MODULE = "backend.storage.vector_store"
_CLASS = "VectorStore"
_CONFIG_MODULE = "backend.storage.vector_config"
_CONFIG_CLASS = "VectorConfig"
_UPSERT = ("upsert_documents", "add_documents", "upsert", "add")
_EXISTS = ("get", "count", "exists", "has")
_MEMORY_PATH = "/dev/shm/l23-vector-store"
_COLLECTION = "review_default"


class VectorStoreWriterAdapter:
    def __init__(self, store: Any | None = None) -> None:
        self._store = store if store is not None else _load_store()
        self._fallback: dict[str, str] = {}

    @property
    def backend(self) -> str:
        return "real" if self._store is not None else "fallback"

    def upsert(self, chunk_id: str, content: str, metadata: dict) -> None:
        if self._store is None:
            self._fallback[chunk_id] = content
            return
        doc = {"id": chunk_id, "content": content, **metadata}
        if _try_upsert(self._store, chunk_id, content, doc):
            return
        self._fallback[chunk_id] = content

    def exists(self, chunk_id: str) -> bool:
        if chunk_id in self._fallback:
            return True
        if self._store is None:
            return False
        return _try_exists(self._store, chunk_id)


def _try_upsert(store: Any, chunk_id: str, content: str, doc: dict) -> bool:
    for name in _UPSERT:
        fn = getattr(store, name, None)
        if not callable(fn):
            continue
        for args in (([doc],), ([chunk_id], [doc]), (chunk_id, content), ([doc],)):
            try:
                fn(*args)
                return True
            except TypeError:
                continue
            except Exception:
                break
    return False


def _try_exists(store: Any, chunk_id: str) -> bool:
    for name in _EXISTS:
        fn = getattr(store, name, None)
        if not callable(fn):
            continue
        try:
            if name == "count":
                return bool(fn())
            result = fn([chunk_id]) if name == "get" else fn(chunk_id)
            return bool(result)
        except TypeError:
            continue
        except Exception:
            continue
    return False


def _load_store() -> Any | None:
    try:
        vs_mod = importlib.import_module(_MODULE)
    except Exception:
        return None
    cls = getattr(vs_mod, _CLASS, None)
    if cls is None:
        return None
    config = _build_config()
    if config is None:
        return None
    try:
        return cls(config)
    except Exception:
        return None


def _build_config() -> Any | None:
    try:
        cfg_mod = importlib.import_module(_CONFIG_MODULE)
    except Exception:
        return None
    cls = getattr(cfg_mod, _CONFIG_CLASS, None)
    if cls is None:
        return None
    for kwargs in (
        {"path": _MEMORY_PATH, "collection_name": _COLLECTION},
        {"path": _MEMORY_PATH},
        {"collection_name": _COLLECTION},
        {},
    ):
        try:
            return cls(**kwargs)
        except Exception:
            continue
    return None


def build_writer(store: Any | None = None) -> VectorStoreWriterAdapter:
    return VectorStoreWriterAdapter(store)
