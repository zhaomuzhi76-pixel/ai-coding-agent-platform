from __future__ import annotations

from backend.runtime.contracts.runtime_graph import RuntimeGraph


class RuntimeExecutionPlan:
    """
    Runtime execution topology value.

    Owns:
        - execution graph topology

    Does not own:
        - validation
        - scheduling
        - execution
        - lifecycle
        - persistence
    """

    VERSION = "3.0"

    def __init__(self, *, graph: RuntimeGraph) -> None:
        if not isinstance(graph, RuntimeGraph):
            raise TypeError("graph must RuntimeGraph")
        self.graph = graph

    def node_count(self) -> int:
        return self.graph.node_count()

    def ready(self) -> bool:
        return self.graph.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "node_count": self.node_count(),
        }


__all__ = ["RuntimeExecutionPlan"]
