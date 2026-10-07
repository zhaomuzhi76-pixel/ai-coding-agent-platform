from __future__ import annotations

import json

from datetime import datetime
from backend.core.contracts.value import CoreValue


SerializerInput = object


class ResultSerializer:
    """
    Stable result serialization implementation owned by core.

    Responsibility:
        - convert result objects into transport-safe values
        - serialize result objects to JSON

    Not Responsible:
        - result creation
        - execution
        - persistence
        - response transport
    """

    VERSION = "1.1"
    MAX_DEPTH = 20

    @classmethod
    def to_dict(
        cls,
        result: SerializerInput,
    ) -> dict[str, CoreValue]:
        value = cls._convert(
            result,
            set(),
            0,
        )

        if isinstance(
            value,
            dict,
        ):
            return value

        return {
            "result": value,
        }

    @classmethod
    def to_json(
        cls,
        result: SerializerInput,
    ) -> str:
        return json.dumps(
            cls.to_dict(result),
            ensure_ascii=False,
        )

    @classmethod
    def _convert(
        cls,
        value: SerializerInput,
        active_stack: set[int],
        depth: int,
    ) -> CoreValue:
        if depth > cls.MAX_DEPTH:
            return "<max_depth_exceeded>"

        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        if isinstance(
            value,
            datetime,
        ):
            return value.isoformat()

        object_id = id(value)

        if object_id in active_stack:
            return "<circular_reference>"

        active_stack.add(
            object_id
        )

        try:
            if isinstance(
                value,
                dict,
            ):
                return {
                    str(key):
                    cls._convert(
                        item,
                        active_stack,
                        depth + 1,
                    )
                    for key, item
                    in value.items()
                }

            if isinstance(
                value,
                (
                    list,
                    tuple,
                    set,
                ),
            ):
                return [
                    cls._convert(
                        item,
                        active_stack,
                        depth + 1,
                    )
                    for item in value
                ]

            dump = getattr(
                value,
                "dump",
                None,
            )

            if callable(dump):
                return cls._convert(
                    dump(),
                    active_stack,
                    depth + 1,
                )

            to_dict = getattr(
                value,
                "to_dict",
                None,
            )

            if callable(to_dict):
                return cls._convert(
                    to_dict(),
                    active_stack,
                    depth + 1,
                )

            if hasattr(
                value,
                "__dict__",
            ):
                return cls._convert(
                    vars(value),
                    active_stack,
                    depth + 1,
                )

            return str(value)
        finally:
            active_stack.remove(
                object_id
            )

    @classmethod
    def ready(
        cls,
    ) -> bool:
        return cls.MAX_DEPTH > 0

    @classmethod
    def dump(
        cls,
    ) -> dict[str, CoreValue]:
        return {
            "name": "ResultSerializer",
            "version": cls.VERSION,
            "max_depth": cls.MAX_DEPTH,
            "ready": cls.ready(),
        }


__all__ = [
    "ResultSerializer",
]
