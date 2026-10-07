from __future__ import annotations

from collections.abc import Sequence

from backend.runtime.contracts.runtime_graph import RuntimeGraph
from backend.core.execution import ExecutionNodeProtocol


class EmptyRoundPolicy:
    """
    Empty scheduler round safety policy.

    Owns:
        - semantic handling of an empty executable selection

    Does not own:
        - completion
        - node selection
        - execution
        - state mutation
        - persistence
    """

    VERSION = "1.0"

    def validate(
        self,
        graph: RuntimeGraph,
        nodes: Sequence[ExecutionNodeProtocol],
    ) -> None:
        if not isinstance(graph, RuntimeGraph):
            raise TypeError(
                "graph must RuntimeGraph"
            )

        if nodes is None:
            raise ValueError(
                "selected nodes required"
            )

        if not nodes:
            raise RuntimeError(
                "scheduler selected no executable nodes"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "EmptyRoundPolicy",
]
