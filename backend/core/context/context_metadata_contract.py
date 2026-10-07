from __future__ import annotations

from typing import TypedDict

from backend.core.contracts.value import CoreValue


class ContextMetadataSnapshot(TypedDict):
    """Context metadata snapshot contract."""

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    metadata: dict[str, CoreValue]


__all__ = [
    "ContextMetadataSnapshot",
]
