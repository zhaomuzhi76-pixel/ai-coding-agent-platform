from __future__ import annotations

from typing import Optional

from backend.core.module.base_manager import (
    BaseManager,
)
from backend.core.module.lifecycle import (
    BaseLifecycle,
)
from backend.core.module.health import (
    BaseHealth,
)
from backend.knowledge.repository import (
    KnowledgeRepository,
)


class KnowledgeManager(
    BaseManager,
    BaseLifecycle,
    BaseHealth,
):
    """
    Knowledge subsystem manager.

    Responsibility:
        - manage knowledge resources
        - provide repository access

    Not Responsible:
        - search logic
        - ranking logic
        - learning logic
        - LLM execution
    """

    VERSION = "8.1"

    def __init__(
        self,
        storage_path: str = "data/knowledge_store.json",
    ) -> None:
        BaseManager.__init__(
            self,
            name="knowledge_manager",
        )

        self.storage_path = storage_path
        self._repository: Optional[
            KnowledgeRepository
        ] = None

    def on_initialize(
        self,
    ) -> None:
        """
        Initialize knowledge repository.
        """
        self._repository = KnowledgeRepository(
            self.storage_path
        )

    def on_start(
        self,
    ) -> None:
        """
        Ensure the knowledge resource is available before use.

        The base lifecycle exposes initialize/start separately, but
        KnowledgeManager must remain restart-safe when callers invoke
        start directly after a previous stop.
        """
        if self._repository is None:
            self.on_initialize()

    def on_shutdown(
        self,
    ) -> None:
        """
        Release knowledge resources.
        """
        self._repository = None

    def repository(
        self,
    ) -> KnowledgeRepository:
        """
        Return knowledge repository.
        """
        if self._repository is None:
            raise RuntimeError(
                "KnowledgeManager not initialized"
            )

        return self._repository


__all__ = [
    "KnowledgeManager",
]
