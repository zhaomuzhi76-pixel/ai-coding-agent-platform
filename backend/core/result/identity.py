from __future__ import annotations

from uuid import uuid4

from backend.core.contracts.timestamp import (
    now_timestamp,
)


class ResultIdentity:
    """
    Stable execution result identity.

    Owns:
        - result id
        - creation timestamp

    Does not own:
        - execution status
        - serialization
        - persistence
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self._result_id = (
            f"res_{uuid4().hex}"
        )
        self._created_at = (
            now_timestamp()
        )

    @property
    def result_id(
        self,
    ) -> str:
        return self._result_id

    @property
    def created_at(
        self,
    ) -> str:
        return self._created_at

    def ready(
        self,
    ) -> bool:
        return bool(
            self._result_id
            and self._created_at
        )

    def dump(
        self,
    ) -> dict[str, str | bool]:
        return {
            "result_id": self.result_id,
            "created_at": self.created_at,
            "ready": self.ready(),
        }


__all__ = [
    "ResultIdentity",
]
