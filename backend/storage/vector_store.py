from __future__ import annotations

from typing import Any

import chromadb

from backend.storage.vector_config import VectorConfig
from backend.storage.vector_health import VectorHealth


class VectorStore:
    VERSION = "5.0"

    def __init__(
        self,
        config: VectorConfig,
    ) -> None:
        if not isinstance(config, VectorConfig):
            raise TypeError("config must be VectorConfig")
        self.config = config
        self.client = chromadb.PersistentClient(
            path=self.config.path,
        )
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=None,
        )
        self.health_checker = VectorHealth(self)

    @property
    def collection_name(self) -> str:
        return self.config.collection_name

    @property
    def embedding_model(self) -> str:
        return self.config.embedding_model

    def reload(self) -> None:
        """重建 collection 引用（clear 后使用，幂等且开销极小）。"""
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=None,
        )

    def add_documents(
        self,
        documents: list[str],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> dict[str, object]:
        self._require_embeddings(embeddings)
        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadata,
            embeddings=embeddings,
        )
        return {
            "success": True,
            "count": len(documents),
            "version": self.VERSION,
        }

    def upsert_documents(
        self,
        documents: list[str],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> dict[str, object]:
        self._require_embeddings(embeddings)
        self.collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadata,
            embeddings=embeddings,
        )
        return {
            "success": True,
            "count": len(documents),
            "version": self.VERSION,
        }

    def search(
        self,
        query_embeddings: list[list[float]],
        limit: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not query_embeddings:
            raise ValueError("query_embeddings required")
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=limit,
            where=where,
        )

    def get(self, ids: list[str]) -> dict[str, Any]:
        return self.collection.get(ids=ids)

    def delete(self, ids: list[str]) -> dict[str, object]:
        self.collection.delete(ids=ids)
        return {
            "success": True,
            "deleted": len(ids),
            "version": self.VERSION,
        }

    def count(self) -> int:
        return self.collection.count()

    def health(self) -> dict[str, object]:
        return self.health_checker.report()

    def _require_embeddings(
        self,
        embeddings: list[list[float]] | None,
    ) -> None:
        if embeddings is None:
            raise ValueError(
                "embeddings required, use external EmbeddingService"
            )

    def dump(self) -> dict[str, object]:
        return {
            "name": "VectorStore",
            "version": self.VERSION,
            "collection": self.collection_name,
            "health": self.health_checker.dump(),
        }


__all__ = ["VectorStore"]
