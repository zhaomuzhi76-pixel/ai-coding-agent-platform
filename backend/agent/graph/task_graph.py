from __future__ import annotations

from typing import Any

from .node import TaskNode


class TaskGraph:
    """
    Runtime DAG graph container.

    Responsibility:

        - store nodes
        - query graph structure

    Not Responsible:

        - execution
        - scheduling
        - lifecycle transition
        - retry
        - persistence
    """

    VERSION = "15.0"

    RESPONSIBILITY = (
        "runtime_dag_graph_container",
    )


    def __init__(
        self,
    ) -> None:

        self._nodes: dict[str, TaskNode] = {}


    @property
    def nodes(
        self,
    ) -> dict[str, TaskNode]:

        return dict(
            self._nodes
        )


    def add_node(
        self,
        node: TaskNode,
    ) -> None:

        if not isinstance(
            node,
            TaskNode,
        ):
            raise TypeError(
                "node must be TaskNode"
            )

        if node.node_id in self._nodes:
            raise ValueError(
                f"duplicate node id:{node.node_id}"
            )

        self._nodes[node.node_id] = node


    def get_node(
        self,
        node_id: str,
    ) -> TaskNode | None:

        return self._nodes.get(
            node_id
        )


    def require_node(
        self,
        node_id: str,
    ) -> TaskNode:

        node = self.get_node(
            node_id
        )

        if node is None:
            raise KeyError(
                f"node missing:{node_id}"
            )

        return node


    def all_nodes(
        self,
    ) -> list[TaskNode]:

        return list(
            self._nodes.values()
        )


    def node_count(
        self,
    ) -> int:

        return len(
            self._nodes
        )


    def empty(
        self,
    ) -> bool:

        return not self._nodes


    def finished_nodes(
        self,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes.values()
            if node.is_finished()
        ]


    def snapshot(
        self,
    ) -> tuple[tuple[str, str], ...]:

        return tuple(
            (
                node.node_id,
                node.status.value,
            )
            for node in self._nodes.values()
        )


    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "version": self.VERSION,
            "nodes": [
                node.to_dict()
                for node in self._nodes.values()
            ],
        }


    def ready(
        self,
    ) -> bool:

        return True


    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name": "TaskGraph",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "nodes": self.node_count(),
            "ready": self.ready(),
        }


__all__ = [
    "TaskGraph",
]
