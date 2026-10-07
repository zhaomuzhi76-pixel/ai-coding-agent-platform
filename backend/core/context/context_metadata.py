from __future__ import annotations

from copy import deepcopy
from typing import Final

from backend.core.context.context_metadata_contract import (
    ContextMetadataSnapshot,
)
from backend.core.context.context_metadata_validator import (
    ContextMetadataValidator,
)
from backend.core.contracts.value import CoreValue


class ContextMetadata:
    """Runtime context metadata container."""

    VERSION = "5.0"

    RESPONSIBILITY: Final = (
        "context_metadata_management",
        "context_metadata_snapshot",
    )

    def __init__(
        self,
    ) -> None:
        self._metadata: dict[
            str,
            CoreValue,
        ] = {}

    def set(
        self,
        key: str,
        value: CoreValue,
    ) -> None:
        if not isinstance(
            key,
            str,
        ) or not key.strip():
            raise ValueError(
                "metadata key required"
            )

        ContextMetadataValidator.validate(
            value
        )

        self._metadata[
            key.strip()
        ] = deepcopy(value)

    def get(
        self,
        key: str,
        default: CoreValue | None = None,
    ) -> CoreValue | None:
        value = self._metadata.get(
            key,
            default,
        )

        return deepcopy(
            value
        )

    def remove(
        self,
        key: str,
    ) -> None:
        self._metadata.pop(
            key,
            None,
        )

    def clear(
        self,
    ) -> None:
        self._metadata.clear()

    def ready(
        self,
    ) -> bool:
        return isinstance(
            self._metadata,
            dict,
        )

    def snapshot(
        self,
    ) -> dict[str, CoreValue]:
        return deepcopy(
            self._metadata
        )

    def dump(
        self,
    ) -> ContextMetadataSnapshot:
        return {
            "name": "ContextMetadata",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "metadata": self.snapshot(),
        }


__all__ = [
    "ContextMetadata",
]
