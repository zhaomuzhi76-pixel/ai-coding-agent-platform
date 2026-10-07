from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from backend.utils.time import now_iso


@dataclass(slots=True)
class RuntimeInstance:
    """
    Runtime execution identity entity.

    Responsibility:

        - maintain runtime identity
        - bind runtime with session
        - maintain execution references


    Not Responsible:

        - persistence
        - event storage
        - result storage
        - execution scheduling
        - recovery
    """

    runtime_id: str

    session_id: str

    execution_id: str | None = None

    graph_id: str | None = None

    status: str = "created"

    metadata: dict = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=now_iso
    )

    updated_at: str = field(
        default_factory=now_iso
    )


    def bind_execution(
        self,
        execution_id: str,
        graph_id: str | None = None,
    ) -> None:

        self.execution_id = execution_id

        self.graph_id = graph_id

        self.updated_at = now_iso()


    def _set_status(
        self,
        status: str,
    ) -> None:

        self.status = status

        self.updated_at = now_iso()


    def update_metadata(
        self,
        key: str,
        value,
    ) -> None:

        self.metadata[key] = value

        self.updated_at = now_iso()


    def dump(
        self,
    ) -> dict:

        return {
            "runtime_id": self.runtime_id,
            "session_id": self.session_id,
            "execution_id": self.execution_id,
            "graph_id": self.graph_id,
            "status": self.status,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


__all__ = [
    "RuntimeInstance",
]
