from __future__ import annotations

from typing import Any


class KnowledgeMatcherRecords:
    """
    Normalize persisted knowledge objects into matcher records.

    Responsibility:
        - convert service/repository knowledge objects
        - preserve stable matcher-facing fields
        - reject unsupported records

    Not Responsible:
        - matching
        - scoring
        - persistence
        - learning
    """

    _FIELDS = (
        "item_id",
        "content",
        "knowledge_type",
    )

    @classmethod
    def normalize(
        cls,
        memory: Any,
    ) -> dict[str, Any]:
        if isinstance(memory, dict):
            return cls._from_mapping(memory)

        dumped = cls._dump_model(memory)

        if dumped is not None:
            return cls._from_mapping(dumped)

        values: dict[str, Any] = {}

        for field in cls._FIELDS:
            if hasattr(memory, field):
                values[field] = getattr(
                    memory,
                    field,
                )

        if "content" not in values:
            raise TypeError(
                "unsupported knowledge record"
            )

        return values

    @classmethod
    def normalize_many(
        cls,
        memories: list[Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(
            memories,
            list,
        ):
            raise TypeError(
                "memories must be list"
            )

        return [
            cls.normalize(memory)
            for memory in memories
        ]

    @classmethod
    def _from_mapping(
        cls,
        memory: dict[str, Any],
    ) -> dict[str, Any]:
        content = memory.get(
            "content",
            "",
        )

        if not isinstance(
            content,
            str,
        ):
            raise TypeError(
                "memory content must be str"
            )

        return {
            field: memory.get(field)
            for field in cls._FIELDS
            if field in memory
        }

    @staticmethod
    def _dump_model(
        memory: Any,
    ) -> dict[str, Any] | None:
        model_dump = getattr(
            memory,
            "model_dump",
            None,
        )

        if callable(model_dump):
            value = model_dump()

            if isinstance(value, dict):
                return value

        to_dict = getattr(
            memory,
            "to_dict",
            None,
        )

        if callable(to_dict):
            value = to_dict()

            if isinstance(value, dict):
                return value

        return None


__all__ = [
    "KnowledgeMatcherRecords",
]
