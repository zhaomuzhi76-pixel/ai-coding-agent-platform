"""
Runtime Session Entity

Responsibility:

    - maintain runtime session identity
    - maintain runtime binding
    - maintain session metadata


Not Responsible:

    - event persistence
    - result persistence
    - runtime execution state persistence
    - scheduling
    - recovery
"""

from __future__ import annotations


from dataclasses import (
    dataclass,
    field,
)


from backend.utils.time import now_iso



@dataclass(slots=True)
class RuntimeSession:

    session_id: str

    runtime_id: str | None = None

    status: str = "created"

    execution_id: str | None = None

    graph_id: str | None = None

    state: dict = field(
        default_factory=dict
    )

    metadata: dict = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=now_iso
    )

    updated_at: str = field(
        default_factory=now_iso
    )


    def bind_runtime(
        self,
        runtime_id: str,
    ) -> None:

        if not runtime_id:

            raise ValueError(
                "runtime_id required"
            )

        self.runtime_id = runtime_id

        self.updated_at = now_iso()



    def _set_status(
        self,
        status: str,
    ) -> None:

        self.status = status

        self.updated_at = now_iso()



    def update_state(
        self,
        key: str,
        value,
    ) -> None:

        self.state[key] = value

        self.updated_at = now_iso()



    def set_execution(
        self,
        execution_id: str,
        graph_id: str | None = None,
    ) -> None:

        self.execution_id = execution_id

        self.graph_id = graph_id

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

            "session_id":
                self.session_id,

            "runtime_id":
                self.runtime_id,

            "status":
                self.status,

            "execution_id":
                self.execution_id,

            "graph_id":
                self.graph_id,

            "state":
                dict(self.state),

            "metadata":
                dict(self.metadata),

            "created_at":
                self.created_at,

            "updated_at":
                self.updated_at,
        }



__all__ = [
    "RuntimeSession",
]
