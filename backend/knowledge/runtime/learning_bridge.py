from __future__ import annotations

from typing import Any

from backend.knowledge.learner import KnowledgeLearner
from backend.knowledge.schema import KnowledgeItem


class KnowledgeLearningBridge:
    """
    Execution-success to persistent learning bridge.

    Responsibility:
        - translate successful request lifecycle into learning input
        - delegate learning to KnowledgeLearner

    Not Responsible:
        - classification
        - persistence
        - retrieval
        - execution orchestration
    """

    VERSION = "1.0"

    def __init__(
        self,
        learner: KnowledgeLearner,
    ) -> None:
        if not isinstance(
            learner,
            KnowledgeLearner,
        ):
            raise TypeError(
                "learner must be KnowledgeLearner"
            )

        self.learner = learner

    def learn_from_request(
        self,
        request: Any,
    ) -> KnowledgeItem | None:
        message = getattr(
            request,
            "message",
            None,
        )

        if not isinstance(
            message,
            str,
        ) or not message.strip():
            raise ValueError(
                "request message required"
            )

        return self.learner.learn(
            message
        )

    def ready(
        self,
    ) -> bool:
        return self.learner.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "learner": type(
                self.learner
            ).__name__,
        }


__all__ = [
    "KnowledgeLearningBridge",
]
