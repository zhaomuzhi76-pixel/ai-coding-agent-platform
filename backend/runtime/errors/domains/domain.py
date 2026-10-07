from __future__ import annotations

from enum import StrEnum


class RuntimeErrorDomain(StrEnum):
    """
    Canonical runtime error ownership domains.

    Responsibility:
        - define stable runtime error domain identity

    Not Responsible:
        - error normalization
        - error consumption
        - runtime execution
        - transport formatting
    """

    EVENT = "event"
    EXECUTION = "execution"
    EXECUTOR = "executor"
    TOOL = "tool"
    KERNEL = "kernel"
    PLUGIN_BOOTSTRAP = "plugin_bootstrap"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        return tuple(item.value for item in cls)

    @classmethod
    def contains(
        cls,
        value: str,
    ) -> bool:
        return value in cls.all()

    @classmethod
    def ready(
        cls,
    ) -> bool:
        return len(cls.all()) == 6


__all__ = [
    "RuntimeErrorDomain",
]
