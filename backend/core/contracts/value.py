from __future__ import annotations

from typing import TypeAlias


PrimitiveValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
)


CoreValue: TypeAlias = (
    PrimitiveValue
    | list["CoreValue"]
    | dict[str, "CoreValue"]
)


def is_core_value(
    value: object,
) -> bool:

    if value is None:
        return True

    if isinstance(
        value,
        bool,
    ):
        return True

    if isinstance(
        value,
        (
            str,
            int,
            float,
        ),
    ):
        return True

    if isinstance(
        value,
        list,
    ):
        return all(
            is_core_value(item)
            for item in value
        )

    if isinstance(
        value,
        dict,
    ):
        return all(
            isinstance(
                key,
                str,
            )
            and is_core_value(item)
            for key, item in value.items()
        )

    return False


__all__ = [
    "PrimitiveValue",
    "CoreValue",
    "is_core_value",
]
