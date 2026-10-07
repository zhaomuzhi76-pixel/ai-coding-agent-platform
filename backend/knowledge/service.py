from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
)

from backend.knowledge.knowledge_manager import (
    KnowledgeManager,
)
from backend.knowledge.schema import (
    KnowledgeItem,
)
from backend.knowledge.types import (
    KnowledgeType,
)


class KnowledgeService:
    """
    Knowledge operation service.

    Responsibility:
        - expose knowledge operations
        - validate manager readiness
        - remember and query knowledge
        - expose permanent rules
        - remove knowledge

    Not Responsible:
        - persistence implementation
        - learning classification
        - ranking
        - LLM execution
    """

    VERSION = "2.0"
    RESPONSIBILITY = (
        "knowledge_operation_service",
    )

    def __init__(
        self,
        manager: KnowledgeManager,
    ) -> None:
        if manager is None:
            raise ValueError(
                "knowledge manager required"
            )

        if not isinstance(
            manager,
            KnowledgeManager,
        ):
            raise TypeError(
                "manager must be KnowledgeManager"
            )

        self.manager = manager

    def repository(self):
        if not self.manager.ready():
            raise RuntimeError(
                "knowledge manager not ready"
            )

        return self.manager.repository()

    def remember(
        self,
        content: str,
        knowledge_type: str,
        importance: int = 5,
        metadata: Dict[str, Any] | None = None,
    ) -> KnowledgeItem:
        if not isinstance(
            content,
            str,
        ) or not content.strip():
            raise ValueError(
                "content required"
            )

        if not isinstance(
            knowledge_type,
            str,
        ) or not knowledge_type.strip():
            raise ValueError(
                "knowledge type required"
            )

        if not isinstance(
            importance,
            int,
        ) or importance < 0:
            raise ValueError(
                "importance must be non-negative int"
            )

        item = KnowledgeItem(
            content=content,
            knowledge_type=knowledge_type,
            importance=importance,
            metadata=dict(
                metadata or {}
            ),
        )

        if not item.ready():
            raise RuntimeError(
                "knowledge item unavailable"
            )

        self.repository().save(item)
        return item

    def get_all(
        self,
    ) -> List[Dict[str, Any]]:
        return self.repository().get_all()

    def find_by_type(
        self,
        knowledge_type: str,
    ) -> List[Dict[str, Any]]:
        if not isinstance(
            knowledge_type,
            str,
        ) or not knowledge_type.strip():
            raise ValueError(
                "knowledge type required"
            )

        return self.repository().find_by_type(
            knowledge_type
        )

    def get_rules(
        self,
    ) -> List[Dict[str, Any]]:
        result = []

        rule_types = (
            KnowledgeType.USER_RULE,
            KnowledgeType.PROJECT_RULE,
            KnowledgeType.CODING_STYLE,
            KnowledgeType.WORKFLOW_RULE,
        )

        for item_type in rule_types:
            result.extend(
                self.find_by_type(
                    item_type
                )
            )

        return result

    def forget(
        self,
        item_id: str,
    ) -> bool:
        if not isinstance(
            item_id,
            str,
        ) or not item_id.strip():
            raise ValueError(
                "item id required"
            )

        return self.repository().delete(
            item_id
        )

    def count(
        self,
    ) -> int:
        return self.repository().count()

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.manager,
                KnowledgeManager,
            )
            and self.manager.ready()
            and callable(
                getattr(
                    self.manager,
                    "repository",
                    None,
                )
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "manager": (
                self.manager.__class__.__name__
            ),
            "count": (
                self.count()
                if self.ready()
                else 0
            ),
        }


__all__ = [
    "KnowledgeService",
]
