from __future__ import annotations

from typing import Optional

from backend.knowledge.schema import (
    KnowledgeItem,
)
from backend.knowledge.service import (
    KnowledgeService,
)
from backend.knowledge.types import (
    KnowledgeType,
    get_default_importance,
)


class KnowledgeLearner:
    """
    Knowledge learning boundary.

    Responsibility:
        - classify incoming messages
        - create persistent knowledge through KnowledgeService

    Not Responsible:
        - persistence implementation
        - retrieval
        - ranking
        - LLM execution
        - application lifecycle
    """

    VERSION = "2.0"
    RESPONSIBILITY = (
        "knowledge_learning_boundary",
    )

    def __init__(
        self,
        service: KnowledgeService,
    ) -> None:
        if service is None:
            raise ValueError(
                "knowledge service required"
            )

        if not isinstance(
            service,
            KnowledgeService,
        ):
            raise TypeError(
                "service must be KnowledgeService"
            )

        self.service = service
        self.learn_count = 0
        self.skipped_count = 0

    def classify(
        self,
        message: str,
    ) -> Optional[str]:
        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "message must be str"
            )

        text = message.strip().lower()

        if not text:
            return None

        rules = (
            (
                KnowledgeType.USER_RULE,
                (
                    "以后",
                    "必须",
                    "不要",
                    "禁止",
                    "要求",
                    "规范",
                ),
            ),
            (
                KnowledgeType.PROJECT_RULE,
                (
                    "项目",
                    "架构",
                    "采用",
                    "使用",
                    "技术栈",
                ),
            ),
            (
                KnowledgeType.ERROR_SOLUTION,
                (
                    "报错",
                    "解决",
                    "原因",
                    "修复",
                    "错误",
                ),
            ),
        )

        for knowledge_type, keywords in rules:
            if any(
                keyword in text
                for keyword in keywords
            ):
                return knowledge_type

        return None

    def learn(
        self,
        message: str,
    ) -> Optional[KnowledgeItem]:
        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "message must be str"
            )

        if not self.service.ready():
            raise RuntimeError(
                "knowledge service not ready"
            )

        knowledge_type = self.classify(
            message
        )

        if knowledge_type is None:
            self.skipped_count += 1
            return None

        item = self.service.remember(
            content=message.strip(),
            knowledge_type=knowledge_type,
            importance=get_default_importance(
                knowledge_type
            ),
        )

        self.learn_count += 1
        return item

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.service,
                KnowledgeService,
            )
            and self.service.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "learn_count": self.learn_count,
            "skipped_count": self.skipped_count,
            "service": type(
                self.service
            ).__name__,
        }


__all__ = [
    "KnowledgeLearner",
]
