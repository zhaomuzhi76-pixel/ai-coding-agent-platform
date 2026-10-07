from __future__ import annotations

from typing import Any, Iterable

from backend.agent.graph.contracts import (
    GraphBuildItemProtocol,
)
from backend.agent.graph.node import TaskNode
from backend.agent.graph.task_graph import TaskGraph


class GraphBuilder:
    """
    Generic task graph construction boundary.

    Graph construction is independent from Planner.
    Any external module implementing GraphBuildItemProtocol
    can provide graph input.
    """

    VERSION = "18.0"
    RESPONSIBILITY = (
        "generic_graph_construction",
    )

    def __init__(self) -> None:
        self.build_count = 0

    def build(
        self,
        items: Iterable[GraphBuildItemProtocol],
    ) -> TaskGraph:
        if items is None:
            raise ValueError("graph items required")

        graph = TaskGraph()

        for index, item in enumerate(items):
            graph.add_node(
                self._create_node(
                    item,
                    index,
                )
            )

        self.build_count += 1
        return graph

    def _create_node(
        self,
        item: GraphBuildItemProtocol,
        index: int,
    ) -> TaskNode:
        if not isinstance(
            item,
            GraphBuildItemProtocol,
        ):
            raise TypeError(
                "item must implement GraphBuildItemProtocol"
            )

        if not item.executor_type:
            raise ValueError(
                "executor_type required"
            )

        return TaskNode(
            node_id=(
                item.node_id
                or f"node_{index}"
            ),
            node_type=item.node_type,
            executor_type=item.executor_type,
            description=item.description,
            depends_on=list(
                item.depends_on
            ),
            input=dict(
                item.parameters
            ),
            metadata=dict(
                item.metadata
            ),
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "build_count": self.build_count,
        }


__all__ = [
    "GraphBuilder",
]
