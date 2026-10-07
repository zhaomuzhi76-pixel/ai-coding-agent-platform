from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.contracts.value import (
    CoreValue,
    is_core_value,
)


class ContextMetadataValidator:
    """Validate context metadata values against the core value domain."""

    VERSION = "3.0"

    RESPONSIBILITY = (
        "context_metadata_validation",
    )

    @classmethod
    def validate(
        cls,
        value: CoreValue,
    ) -> None:
        if not is_core_value(value):
            raise TypeError(
                "unsupported metadata value type"
            )

    @classmethod
    def ready(
        cls,
    ) -> bool:
        return bool(
            cls.VERSION
            and cls.RESPONSIBILITY
        )

    @classmethod
    def dump(
        cls,
    ) -> dict[str, CoreValue]:
        return {
            "name": "ContextMetadataValidator",
            "version": cls.VERSION,
            "responsibility": cls.RESPONSIBILITY,
            "ready": cls.ready(),
        }


__all__ = [
    "ContextMetadataValidator",
]
