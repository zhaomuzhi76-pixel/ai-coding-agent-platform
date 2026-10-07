from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.contracts.value import (
    CoreValue,
    is_core_value,
)


class ExecutionOutputValidator:
    """Validate execution output values against the core value domain."""

    VERSION = "3.0"

    RESPONSIBILITY = (
        "execution_output_value_validation",
    )

    @classmethod
    def validate(
        cls,
        value: CoreValue,
    ) -> None:
        if not is_core_value(value):
            raise TypeError(
                "unsupported execution output value type"
            )

    @classmethod
    def validate_snapshot(
        cls,
        snapshot: CoreValue,
    ) -> None:
        if not isinstance(
            snapshot,
            dict,
        ):
            raise TypeError(
                "output payload dump must return dict"
            )

        if not is_core_value(snapshot):
            raise TypeError(
                "output payload contains unsupported value"
            )

    @classmethod
    def ready(
        cls,
    ) -> bool:
        return (
            callable(cls.validate)
            and callable(cls.validate_snapshot)
        )

    @classmethod
    def dump(
        cls,
    ) -> dict[str, CoreValue]:
        return {
            "name": "ExecutionOutputValidator",
            "version": cls.VERSION,
            "responsibility": cls.RESPONSIBILITY,
            "ready": cls.ready(),
        }


__all__ = [
    "ExecutionOutputValidator",
]
