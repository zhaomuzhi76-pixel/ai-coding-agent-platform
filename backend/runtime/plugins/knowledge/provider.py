from __future__ import annotations

import os
from pathlib import Path

from backend.knowledge.knowledge_manager import KnowledgeManager
from backend.knowledge.learner import KnowledgeLearner
from backend.knowledge.matcher import KnowledgeMatcher
from backend.knowledge.runtime.injector import KnowledgeInjector
from backend.knowledge.runtime.learning_bridge import (
    KnowledgeLearningBridge,
)
from backend.knowledge.runtime.middleware import (
    KnowledgeMiddleware,
)
from backend.knowledge.service import KnowledgeService


class KnowledgeRuntimeCapabilityProvider:
    """
    Runtime provider for the persistent knowledge capability.

    Responsibility:
        - own knowledge runtime dependencies
        - create request middleware

    Not Responsible:
        - runtime lifecycle
        - agent lifecycle
        - planner preparation
        - runtime execution
        - transport
        - LLM execution
    """

    VERSION = "1.1"

    def __init__(
        self,
        storage_path: str | None = None,
    ) -> None:
        path = storage_path or os.getenv(
            "KNOWLEDGE_STORAGE_PATH",
            "data/knowledge.json",
        )

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.manager = KnowledgeManager(
            storage_path=path,
        )
        self.manager.start()

        self.service = KnowledgeService(
            self.manager
        )
        self.learner = KnowledgeLearner(
            self.service
        )
        self.matcher = KnowledgeMatcher()
        self.injector = KnowledgeInjector(
            self.service,
            self.matcher,
        )
        self.learning_bridge = (
            KnowledgeLearningBridge(
                self.learner
            )
        )

    def create_middleware(
        self,
    ) -> KnowledgeMiddleware:
        middleware = KnowledgeMiddleware(
            injector=self.injector,
            learning_bridge=self.learning_bridge,
        )

        if not middleware.ready():
            raise RuntimeError(
                "knowledge middleware unavailable"
            )

        return middleware

    def ready(
        self,
    ) -> bool:
        return (
            self.service.ready()
            and self.learner.ready()
            and self.matcher.ready()
            and self.injector.ready()
            and self.learning_bridge.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "service": self.service.dump(),
            "learner": self.learner.dump(),
            "matcher": self.matcher.dump(),
            "injector": self.injector.dump(),
            "learning_bridge": (
                self.learning_bridge.dump()
            ),
        }


__all__ = [
    "KnowledgeRuntimeCapabilityProvider",
]
