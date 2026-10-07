from __future__ import annotations

from typing import Any


class KernelMetadataCarrier:
    """
    Kernel context metadata carrier.

    Responsibility:
        - hold request scoped metadata
        - expose metadata access

    Not Responsible:
        - persistence
        - lifecycle
        - execution
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._metadata: dict[str, Any] = {}

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                "metadata key required"
            )

        self._metadata[key.strip()] = value

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._metadata.get(
            key,
            default,
        )

    def clear(self) -> None:
        self._metadata.clear()

    def dump(self) -> dict[str, Any]:
        return dict(self._metadata)


__all__ = [
    "KernelMetadataCarrier",
]
