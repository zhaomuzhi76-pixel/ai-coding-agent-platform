from __future__ import annotations

from typing import Any


def string_value(
    payload: dict[str, Any],
    name: str,
    default: str,
) -> str:
    value = payload.get(name, default)

    if value is None:
        return default

    if not isinstance(value, str):
        raise TypeError(f"{name} must be str")

    return value


def bool_value(
    payload: dict[str, Any],
    name: str,
    default: bool,
) -> bool:
    value = payload.get(name, default)

    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")

    return value


def float_value(
    payload: dict[str, Any],
    name: str,
    default: float,
) -> float:
    value = payload.get(name, default)

    if isinstance(value, bool):
        raise TypeError(f"{name} must be number")

    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(
            f"{name} must be number"
        ) from error


def optional_int(
    payload: dict[str, Any],
    name: str,
) -> int | None:
    value = payload.get(name)

    if value is None:
        return None

    if isinstance(value, bool):
        raise TypeError(f"{name} must be int")

    if not isinstance(value, int):
        raise TypeError(f"{name} must be int")

    return value


def metadata_value(
    payload: dict[str, Any],
) -> dict[str, Any]:
    value = payload.get(
        "metadata",
        {},
    )

    if not isinstance(value, dict):
        raise TypeError(
            "metadata must be dict"
        )

    return dict(value)


__all__ = [
    "bool_value",
    "float_value",
    "metadata_value",
    "optional_int",
    "string_value",
]
