from __future__ import annotations

from typing import Any

from backend.knowledge.matcher import KnowledgeMatcher
from backend.knowledge.service import KnowledgeService


class KnowledgeInjector:
    """
    Request-scoped knowledge retrieval boundary.

    Responsibility:
        - query persisted knowledge
        - rank matching knowledge
        - inject stable values into KernelContext

    Not Responsible:
        - persistence
        - learning
        - planning
        - runtime execution
    """

    VERSION = "1.0"
    QUERY_KEY = "knowledge.query"
    MATCHES_KEY = "knowledge.matches"
    COUNT_KEY = "knowledge.count"

    def __init__(
        self,
        service: KnowledgeService,
        matcher: KnowledgeMatcher,
        limit: int = 5,
    ) -> None:
        if not isinstance(service, KnowledgeService):
            raise TypeError("service must be KnowledgeService")
        if not isinstance(matcher, KnowledgeMatcher):
            raise TypeError("matcher must be KnowledgeMatcher")
        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be positive int")

        self.service = service
        self.matcher = matcher
        self.limit = limit

    def inject(
        self,
        query: str,
        context: Any,
    ) -> list[dict[str, Any]]:
        self._validate(query, context)

        memories = self.service.get_all()
        matches = self.matcher.match(query, memories)[: self.limit]

        context.set(self.QUERY_KEY, query)
        context.set(self.MATCHES_KEY, matches)
        context.set(self.COUNT_KEY, len(matches))

        return matches

    def ready(self) -> bool:
        return (
            self.service.ready()
            and self.matcher.ready()
            and self.limit > 0
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "limit": self.limit,
            "service": type(self.service).__name__,
            "matcher": type(self.matcher).__name__,
        }

    @staticmethod
    def _validate(query: str, context: Any) -> None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("knowledge query required")
        if context is None or not callable(getattr(context, "set", None)):
            raise TypeError("context must expose set()")


__all__ = ["KnowledgeInjector"]
