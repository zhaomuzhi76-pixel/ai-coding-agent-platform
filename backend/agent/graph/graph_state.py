from __future__ import annotations

from typing import Any

from backend.agent.graph.node_state import NodeState


class GraphState:
    """
    TaskGraph state query helper.

    Responsibility:

        - query node states
        - build execution summary

    Not responsible:

        - execution
        - validation
        - serialization
    """

    VERSION = "2.0"

    def _nodes(
        self,
        graph,
    ) -> list[Any]:
        return graph.all_nodes()

    def success_nodes(
        self,
        graph,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes(graph)
            if node.status == NodeState.SUCCESS
        ]

    def failed_nodes(
        self,
        graph,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes(graph)
            if node.status == NodeState.FAILED
        ]

    def cancelled_nodes(
        self,
        graph,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes(graph)
            if node.status == NodeState.CANCELLED
        ]

    def running_nodes(
        self,
        graph,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes(graph)
            if node.status == NodeState.RUNNING
        ]

    def ready_nodes(
        self,
        graph,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes(graph)
            if node.status == NodeState.READY
        ]

    def pending_nodes(
        self,
        graph,
    ) -> list[str]:

        return [
            node.node_id
            for node in self._nodes(graph)
            if node.status == NodeState.CREATED
        ]

    def is_finished(
        self,
        graph,
    ) -> bool:

        nodes = self._nodes(graph)

        if not nodes:
            return False

        return all(
            node.is_finished()
            for node in nodes
        )

    def summary(
        self,
        graph,
    ) -> dict[str, Any]:

        return {
            "version": self.VERSION,
            "success": self.success_nodes(graph),
            "running": self.running_nodes(graph),
            "ready": self.ready_nodes(graph),
            "pending": self.pending_nodes(graph),
            "failed": self.failed_nodes(graph),
            "cancelled": self.cancelled_nodes(graph),
            "finished": self.is_finished(graph),
        }


__all__ = [
    "GraphState",
]
