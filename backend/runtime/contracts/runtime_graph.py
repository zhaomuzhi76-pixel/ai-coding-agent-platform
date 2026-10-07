from __future__ import annotations

from backend.core.execution import RuntimeExecutionStep


class RuntimeGraph:
    """
    Runtime DAG topology value container.

    Owns:
        - runtime execution nodes
        - topology lookup

    Does not own:
        - validation
        - scheduling
        - execution
        - persistence
    """

    VERSION = "11.0"

    def __init__(self) -> None:
        self._nodes: dict[str, RuntimeExecutionStep] = {}

    def add_node(self, node: RuntimeExecutionStep) -> None:
        if not isinstance(node, RuntimeExecutionStep):
            raise TypeError("node must RuntimeExecutionStep")
        if node.node_id in self._nodes:
            raise ValueError(f"duplicate node id: {node.node_id}")
        self._nodes[node.node_id] = node

    def get_node(
        self,
        node_id: str,
    ) -> RuntimeExecutionStep | None:
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[RuntimeExecutionStep]:
        return list(self._nodes.values())

    def node_ids(self) -> set[str]:
        return set(self._nodes)

    def contains(self, node_id: str) -> bool:
        return node_id in self._nodes

    def node_count(self) -> int:
        return len(self._nodes)

    def ready(self) -> bool:
        return isinstance(self._nodes, dict)

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "node_count": self.node_count(),
        }


__all__ = ["RuntimeGraph"]
