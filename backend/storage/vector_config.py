"""向量库配置。字段来源：参数 > 环境变量 > 默认。
职责：只承载配置与校验。不连库、不做后端选择（vector_backend 管）。
向后兼容：原 4 字段语义不变；新增 backend/qdrant_url/qdrant_api_key。
"""
from __future__ import annotations
from backend.core.model_registry.embedding_resolver import resolve_embedding_model
from backend.config.constants.endpoints import (
    QDRANT_URL,
)

import os


BACKEND_CHROMA = "chroma"
BACKEND_QDRANT = "qdrant"
SUPPORTED_BACKENDS = (BACKEND_CHROMA, BACKEND_QDRANT)


class VectorConfig:
    VERSION = "2.1"

    def __init__(
        self,
        path: str | None = None,
        collection_name: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
        backend: str | None = None,
        qdrant_url: str | None = None,
        qdrant_api_key: str | None = None,
    ) -> None:
        self.path = path or os.getenv("VECTOR_DB_PATH", "./vector_db")
        self.collection_name = collection_name or os.getenv(
            "VECTOR_COLLECTION", "agent_code_knowledge")
        self.embedding_provider = (
            embedding_provider
            or os.getenv("VECTOR_EMBEDDING_PROVIDER", "external")
        )
        self.embedding_model = (
            embedding_model
            or resolve_embedding_model()
        )

        # 新增：后端选择
        self.backend = (backend or os.getenv("VECTOR_BACKEND",
                                              BACKEND_CHROMA)).lower()
        self.qdrant_url = (
            qdrant_url or os.getenv("QDRANT_URL",
                                     QDRANT_URL)
        )
        self.qdrant_api_key = (
            qdrant_api_key or os.getenv("QDRANT_API_KEY", "")
        )

        # 校验
        if not self.path.strip():
            raise ValueError("VECTOR_DB_PATH required")
        if not self.collection_name.strip():
            raise ValueError("VECTOR_COLLECTION required")
        if not self.embedding_provider.strip():
            raise ValueError("VECTOR_EMBEDDING_PROVIDER required")
        if not self.embedding_model.strip():
            raise ValueError("VECTOR_EMBEDDING_MODEL required")
        if self.backend not in SUPPORTED_BACKENDS:
            raise ValueError(
                f"VECTOR_BACKEND must be in {SUPPORTED_BACKENDS}, "
                f"got {self.backend!r}")
        if not self.qdrant_url.strip():
            raise ValueError("QDRANT_URL required when backend=qdrant")

    def dump(self) -> dict:
        return {
            "name": "VectorConfig", "version": self.VERSION,
            "path": self.path, "collection": self.collection_name,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "backend": self.backend,
            "qdrant_url": self.qdrant_url,
        }


__all__ = ["VectorConfig", "BACKEND_CHROMA", "BACKEND_QDRANT",
           "SUPPORTED_BACKENDS"]
