from __future__ import annotations

import re
from typing import Any

from backend.knowledge.matcher_records import (
    KnowledgeMatcherRecords,
)


class KnowledgeMatcher:
    """
    Knowledge retrieval and relevance ranking boundary.

    Responsibility:
        - normalize query/content tokens
        - score knowledge relevance
        - return ranked knowledge records
    """

    VERSION = "2.2"
    RESPONSIBILITY = (
        "knowledge_retrieval_matching",
    )

    _ASCII_TOKEN_PATTERN = re.compile(
        r"[a-z0-9]+(?:'[a-z0-9]+)*",
        re.IGNORECASE,
    )

    def __init__(
        self,
        min_score: int = 1,
    ) -> None:
        if type(min_score) is not int:
            raise TypeError(
                "min_score must be int"
            )

        if min_score < 1:
            raise ValueError(
                "min_score must be positive"
            )

        self.min_score = min_score
        self.match_count = 0

    def match(
        self,
        query: str,
        memories: list[Any],
    ) -> list[dict[str, Any]]:
        self._validate_query(query)

        records = (
            KnowledgeMatcherRecords.normalize_many(
                memories
            )
        )

        self.match_count += 1
        results: list[dict[str, Any]] = []

        for record in records:
            score = self._score(
                query,
                record.get(
                    "content",
                    "",
                ),
            )

            if score < self.min_score:
                continue

            item = dict(record)
            item["score"] = score
            results.append(item)

        results.sort(
            key=lambda item: (
                -item["score"],
                str(
                    item.get(
                        "item_id",
                        "",
                    )
                ),
            )
        )

        return results

    def score(
        self,
        query: str,
        content: str,
    ) -> int:
        self._validate_query(query)

        if not isinstance(
            content,
            str,
        ):
            raise TypeError(
                "content must be str"
            )

        return self._score(
            query,
            content,
        )

    def ready(
        self,
    ) -> bool:
        return self.min_score > 0

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "min_score": self.min_score,
            "match_count": self.match_count,
        }

    def _score(
        self,
        query: str,
        content: str,
    ) -> int:
        query_tokens = set(
            self._tokens(query)
        )
        content_tokens = set(
            self._tokens(content)
        )

        return len(
            query_tokens & content_tokens
        )

    @classmethod
    def _tokens(
        cls,
        text: str,
    ) -> list[str]:
        normalized = text.lower().strip()

        if not normalized:
            return []

        ascii_tokens = (
            cls._ASCII_TOKEN_PATTERN.findall(
                normalized
            )
        )

        cjk_tokens: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            if not buffer:
                return

            value = "".join(buffer)

            if len(value) == 1:
                cjk_tokens.append(value)
            else:
                cjk_tokens.extend(
                    value[index:index + 2]
                    for index in range(
                        len(value) - 1
                    )
                )
                cjk_tokens.append(value)

            buffer.clear()

        for char in normalized:
            if "\u4e00" <= char <= "\u9fff":
                buffer.append(char)
            else:
                flush()

        flush()

        return [
            token
            for token in (
                ascii_tokens
                + cjk_tokens
            )
            if token
        ]

    @staticmethod
    def _validate_query(
        query: str,
    ) -> None:
        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "query must be str"
            )

        if not query.strip():
            raise ValueError(
                "query required"
            )


__all__ = [
    "KnowledgeMatcher",
]
