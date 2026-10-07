from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from backend.agent.graph.node_state import NodeState
@dataclass(eq=False)
class TaskNode:

    VERSION = "10.3"

    RESPONSIBILITY = (
        "graph_node_entity",
    )

    node_id: str

    executor_type: str

    node_type: str

    description: str = ""

    depends_on: list[str] = field(
        default_factory=list
    )

    status: NodeState = NodeState.CREATED

    input: dict[str, Any] = field(
        default_factory=dict
    )

    output: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def parameters(
        self,
    ) -> dict[str, Any]:
        return dict(self.input)

    def __post_init__(
        self,
    ) -> None:

        if not self.node_id:
            raise ValueError(
                "node_id required"
            )

        if not self.executor_type:
            raise ValueError(
                "executor_type required"
            )

        if not self.node_type:
            raise ValueError(
                "node_type required"
            )

    def __hash__(
        self,
    ) -> int:

        return hash(
            self.node_id
        )

    def __eq__(
        self,
        other: object,
    ) -> bool:

        return (
            isinstance(
                other,
                TaskNode,
            )
            and self.node_id == other.node_id
        )

    def ready(
        self,
        finished_nodes: list[str],
    ) -> bool:

        return all(
            item in finished_nodes
            for item in self.depends_on
        )

    def mark_ready(
        self,
    ) -> None:

        if self.status == NodeState.CREATED:
            self.status = NodeState.READY

    def start(
        self,
    ) -> None:

        self._require(
            NodeState.CREATED,
            NodeState.READY,
        )

        self.status = NodeState.RUNNING

    def finish(
        self,
        output: dict[str, Any],
    ) -> None:

        self._require(
            NodeState.RUNNING
        )

        self.output = dict(
            output
        )

        self.status = NodeState.SUCCESS

    def fail(
        self,
        error: str,
    ) -> None:

        self._require(
            NodeState.RUNNING
        )

        self.output = {
            "error": error
        }

        self.status = NodeState.FAILED

    def cancel(
        self,
    ) -> None:

        if self.is_finished():
            raise RuntimeError(
                "node already finished"
            )

        self.status = NodeState.CANCELLED

    def _require(
        self,
        *states: NodeState,
    ) -> None:

        if self.status not in states:
            raise RuntimeError(
                f"invalid state:{self.status}"
            )

    def is_finished(
        self,
    ) -> bool:

        return self.status in {
            NodeState.SUCCESS,
            NodeState.FAILED,
            NodeState.CANCELLED,
        }

    def is_executable(
        self,
    ) -> bool:

        return self.status in {
            NodeState.CREATED,
            NodeState.READY,
        }

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "executor_type": self.executor_type,
            "description": self.description,
            "depends_on": list(
                self.depends_on
            ),
            "status": self.status.value,
            "input": dict(
                self.input
            ),
            "output": dict(
                self.output
            ),
            "metadata": dict(
                self.metadata
            ),
        }

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name": "TaskNode",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "node_id": self.node_id,
            "status": self.status.value,
        }


__all__ = [
    "TaskNode",
]
