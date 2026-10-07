from __future__ import annotations

from typing import Any, TYPE_CHECKING

from backend.core.health.status import HealthStatus

if TYPE_CHECKING:
    from backend.storage.vector_store import VectorStore


class VectorHealth:
    """
    Synchronous vector storage health capability.

    Responsibility:
        - collection availability check
        - vector storage health reporting

    Not Responsible:
        - CRUD operations
        - embedding generation
        - database initialization
        - search execution
    """

    VERSION = "2.0"

    def __init__(
        self,
        store: "VectorStore",
    ) -> None:
        if store is None:
            raise ValueError("vector store required")
        self.store = store

    def check(self) -> HealthStatus:
        try:
            self.store.count()
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY

    def report(self) -> dict[str, object]:
        try:
            count = self.store.count()
            return {
                "status": HealthStatus.HEALTHY.value,
                "provider": "chromadb",
                "collection": self.store.collection_name,
                "count": count,
                "embedding": (
                    self.store.config.embedding_provider
                ),
                "model": (
                    self.store.embedding_model
                ),
                "version": self.VERSION,
            }
        except Exception as error:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "provider": "chromadb",
                "message": str(error),
                "version": self.VERSION,
            }

    def dump(self) -> dict[str, Any]:
        return {
            "name": "VectorHealth",
            "version": self.VERSION,
        }


__all__ = [
    "VectorHealth",
]
