"""Qdrant 辅助工具。职责：id 转换、filter 转换、collection 建表。
不做 CRUD（vector_store_qdrant 管）、不选后端（vector_backend 管）。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import uuid
from typing import Any, Optional


def to_qdrant_id(pid: str):
    """Qdrant id 必须 int 或 UUID。非 UUID 字符串 → 确定性 UUID。"""
    try:
        return int(pid)
    except (TypeError, ValueError):
        pass
    try:
        return uuid.UUID(pid)
    except (ValueError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_OID, str(pid)))


def to_qdrant_filter(where: Optional[dict]) -> Optional[Any]:
    """把 Chroma 风格 where={k: v} 或 {k: {'$eq': v}} 转 Qdrant Filter。"""
    if not where:
        return None
    try:
        from qdrant_client.models import (
            FieldCondition, Filter, MatchValue)
    except ImportError:
        return None
    must: list = []
    for k, v in dict(where).items():
        if isinstance(v, dict) and "$eq" in v:
            v = v["$eq"]
        must.append(FieldCondition(key=str(k), match=MatchValue(value=v)))
    return Filter(must=must) if must else None


def ensure_collection(client, name: str, dim: int,
                       current_dim: Optional[int]) -> int:
    """幂等建 collection。若已存在且维度一致 → 直接返回。"""
    if current_dim == dim:
        return current_dim
    try:
        from qdrant_client.models import Distance, VectorParams
    except ImportError as e:
        raise RuntimeError("qdrant-client 缺 models") from e
    try:
        client.get_collection(name)
    except Exception:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
    return dim


def probe_dim(client, name: str) -> Optional[int]:
    """读取已有 collection 的向量维度。不存在返回 None。"""
    try:
        info = client.get_collection(name)
        vec = getattr(info.config.params, "vectors", None)
        if vec is not None and hasattr(vec, "size"):
            return int(vec.size)
    except Exception as e:
        swallow("storage.qdrant_helpers:67", e)
    return None


def build_client(url: str, api_key: str = "", timeout: int = 10):
    """构造 QdrantClient。直连（不走 http_proxy）。"""
    try:
        from qdrant_client import QdrantClient
    except ImportError as e:
        raise RuntimeError(
            "未安装 qdrant-client，请 pip install qdrant-client") from e
    host = url.replace("http://", "").replace("https://", "").split(":")[0]
    port = int(url.split(":")[-1]) if ":" in url else 6333
    return QdrantClient(
        host=host, port=port,
        api_key=api_key or None,
        timeout=timeout,
        prefer_grpc=False,
        check_compatibility=False,
    )


__all__ = ["to_qdrant_id", "to_qdrant_filter",
           "ensure_collection", "probe_dim", "build_client"]
