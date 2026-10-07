"""
Runtime identity registry.

Responsible:

    - create runtime identity
    - register runtime lifecycle
    - check runtime existence
    - clear runtime identity


Not responsible:

    - session persistence
    - event storage
    - result storage
    - execution state storage
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class RuntimePersistence:

    VERSION = "8.1"

    RESPONSIBILITY = (
        "runtime_identity_registry",
    )

    def __init__(
        self,
    ) -> None:

        self.runtime_ids: set[str] = set()

        self.create_count = 0

        self.clear_count = 0


    def create_runtime_id(
        self,
    ) -> str:

        runtime_id = uuid4().hex

        self.register_runtime(
            runtime_id
        )

        return runtime_id


    def register_runtime(
        self,
        runtime_id: str,
    ) -> None:

        self._validate_runtime_id(
            runtime_id
        )

        self.runtime_ids.add(
            runtime_id
        )

        self.create_count += 1


    def exists(
        self,
        runtime_id: str,
    ) -> bool:

        self._validate_runtime_id(
            runtime_id
        )

        return runtime_id in self.runtime_ids


    def clear_runtime(
        self,
        runtime_id: str,
    ) -> None:

        self._validate_runtime_id(
            runtime_id
        )

        self.runtime_ids.discard(
            runtime_id
        )

        self.clear_count += 1


    def runtime_count(
        self,
    ) -> int:

        return len(
            self.runtime_ids
        )


    def ready(
        self,
    ) -> bool:

        return True


    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "RuntimePersistence",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "runtime_count":
                self.runtime_count(),

            "created":
                self.create_count,

            "cleared":
                self.clear_count,
        }


    def _validate_runtime_id(
        self,
        runtime_id: str,
    ) -> None:

        if not runtime_id:

            raise ValueError(
                "runtime_id required"
            )


runtime_persistence = RuntimePersistence()


__all__ = [
    "RuntimePersistence",
    "runtime_persistence",
]
