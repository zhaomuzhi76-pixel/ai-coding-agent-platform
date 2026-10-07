from __future__ import annotations

from typing import Final
from uuid import uuid4

from backend.utils.time import now_iso


class ExecutionTask:
    """
    Runtime execution task.

    Responsibility:

        - task identity
        - execution payload boundary
        - execution result boundary
        - task snapshot

    Not Responsible:

        - scheduling
        - execution strategy
        - provider routing
        - business logic
    """

    VERSION: Final = "1.0"

    RESPONSIBILITY: Final = (
        "task_identity",
        "task_payload",
        "task_result",
    )

    def __init__(
        self,
        name: str,
        payload: object | None = None,
    ) -> None:

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "task name must be str"
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "task name required"
            )

        self._task_id = (
            f"task_{uuid4().hex}"
        )

        self._name = name

        self._payload = payload

        self._result: object | None = None

        timestamp = now_iso()

        self._created_at = timestamp

        self._updated_at = timestamp

    @property
    def task_id(
        self,
    ) -> str:

        return self._task_id

    @property
    def name(
        self,
    ) -> str:

        return self._name

    @property
    def payload(
        self,
    ) -> object | None:

        return self._payload

    @property
    def result(
        self,
    ) -> object | None:

        return self._result

    def complete(
        self,
        result: object,
    ) -> None:

        self._result = result

        self._updated_at = now_iso()

    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "id": self.task_id,
            "name": self.name,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "payload": self.payload,
            "result": self.result,
            "created_at": self._created_at,
            "updated_at": self._updated_at,
        }


__all__ = [
    "ExecutionTask",
]
