from __future__ import annotations

from typing import TypeAlias


ResultScalar: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
)

ResultValue: TypeAlias = (
    ResultScalar
    | dict[str, "ResultValue"]
    | list["ResultValue"]
)

ResultOutput: TypeAlias = ResultValue

ResultMetadata: TypeAlias = dict[
    str,
    ResultValue,
]


def is_result_value(
    value: object,
) -> bool:
    if value is None:
        return True

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return True

    if isinstance(value, dict):
        return all(
            isinstance(key, str)
            and is_result_value(item)
            for key, item in value.items()
        )

    if isinstance(value, list):
        return all(
            is_result_value(item)
            for item in value
        )

    return False


__all__ = [
    "ResultMetadata",
    "ResultOutput",
    "ResultScalar",
    "ResultValue",
    "is_result_value",
]
