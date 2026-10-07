"""向量库后端选择。职责：按 VectorConfig.backend 返回对应 Store 实例。
不实现存储（vector_store / vector_store_qdrant 各自管）、不配置（VectorConfig 管）。
唯一装配入口：get_vector_store()。调用方零感知后端差异。
"""
from __future__ import annotations
from typing import Any, Optional

from backend.storage.vector_config import (
    BACKEND_CHROMA, BACKEND_QDRANT, VectorConfig)


def get_vector_store(config: Optional[VectorConfig] = None) -> Any:
    """按 config.backend 返回 Chroma 或 Qdrant Store。
    两实现 11 方法完全对齐，调用方无感。"""
    cfg = config or VectorConfig()
    import os as _os
    if _os.getenv("RAG_VECTOR_BACKEND", "lite") == "lite":
        from backend.storage.vector_store_lite import LiteVectorStore
        return LiteVectorStore(cfg)
    if cfg.backend == BACKEND_QDRANT:
        from backend.storage.vector_store_qdrant import QdrantStore
        return QdrantStore(cfg)
    from backend.storage.vector_store import VectorStore
    return VectorStore(cfg)


def current_backend(config: Optional[VectorConfig] = None) -> str:
    return (config or VectorConfig()).backend


__all__ = ["get_vector_store", "current_backend"]
