from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
    asdict,
)
from typing import (
    Any,
    Dict,
    Optional,
)

from backend.utils.time import now_iso


@dataclass
class KnowledgeItem:
    """
    Persistent knowledge unit.

    Responsibility:
        - carry one persistent knowledge record
        - expose readiness
        - expose serialized state
        - support content update

    Not Responsible:
        - persistence
        - retrieval
        - ranking
        - learning
    """

    VERSION = "1.0"
    RESPONSIBILITY = (
        "persistent_knowledge_item",
    )

    content: str
    knowledge_type: str = "GENERAL"
    source: str = "conversation"
    importance: int = 5
    item_id: Optional[str] = None
    created_at: str = field(
        default_factory=now_iso
    )
    updated_at: str = field(
        default_factory=now_iso
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.content,
                str,
            )
            and bool(
                self.content.strip()
            )
            and isinstance(
                self.knowledge_type,
                str,
            )
            and bool(
                self.knowledge_type.strip()
            )
            and isinstance(
                self.source,
                str,
            )
            and bool(
                self.source.strip()
            )
            and isinstance(
                self.importance,
                int,
            )
            and self.importance >= 0
            and isinstance(
                self.created_at,
                str,
            )
            and bool(
                self.created_at
            )
            and isinstance(
                self.updated_at,
                str,
            )
            and bool(
                self.updated_at
            )
            and isinstance(
                self.metadata,
                dict,
            )
        )

    def dump(
        self,
    ) -> Dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            **asdict(self),
        }

    def update(
        self,
        content: str,
    ) -> None:
        if not isinstance(
            content,
            str,
        ) or not content.strip():
            raise ValueError(
                "content required"
            )

        self.content = content
        self.updated_at = now_iso()


@dataclass
class UserPreference:
    """
    User long-term preference.
    """

    key: str
    value: Any
    confidence: float = 1.0
    created_at: str = field(
        default_factory=now_iso
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def dump(
        self,
    ) -> Dict[str, Any]:
        return asdict(
            self
        )


@dataclass
class ProjectRule:
    """
    Project-level permanent rule.
    """

    name: str
    description: str
    priority: int = 5
    enabled: bool = True
    created_at: str = field(
        default_factory=now_iso
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def dump(
        self,
    ) -> Dict[str, Any]:
        return asdict(
            self
        )


__all__ = [
    "KnowledgeItem",
    "UserPreference",
    "ProjectRule",
    "now_iso",
]
