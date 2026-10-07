from __future__ import annotations

from typing import Any

from backend.codebase.graph.builder import (
    CodeGraphBuilder,
)
from backend.codebase.graph.model import (
    CodeGraph,
)
from backend.codebase.graph.query import (
    CodeGraphQuery,
)

class GraphProvider:
    """
    Code graph access and rebuild provider.

    Owns:
        - graph construction from normalized code index
        - graph query access

    Does not own:
        - source parsing
        - indexing
        - persistence
        - code modification
    """

    VERSION = "4.0"

    def __init__(
        self,
        graph: CodeGraph | None = None,
        query: CodeGraphQuery | None = None,
        builder: CodeGraphBuilder | None = None,
    ) -> None:
        self.graph = graph or CodeGraph()
        self.query = (
            query
            or CodeGraphQuery(self.graph)
        )
        self.builder = (
            builder
            or CodeGraphBuilder()
        )
        self.query_count = 0
        self.build_count = 0

    def build(
        self,
        files: list[dict[str, Any]],
    ) -> CodeGraph:
        if not isinstance(files, list):
            raise TypeError(
                "graph input must list"
            )

        self.graph = self.builder.build(
            files
        )
        self.query = CodeGraphQuery(
            self.graph
        )
        self.build_count += 1
        return self.graph

    def get_graph(self) -> CodeGraph:
        return self.graph

    def find_dependents(
        self,
        node_id: str,
    ) -> list[str]:
        self.query_count += 1
        return list(
            self.query.find_dependents(node_id)
        )

    def find_symbols(
        self,
        file_id: str,
    ) -> list[str]:
        self.query_count += 1
        return list(
            self.query.find_symbols(file_id)
        )

    def find_related(
        self,
        node_id: str,
    ) -> list[str]:
        self.query_count += 1
        return list(
            self.query.find_related(node_id)
        )

    def find_nodes_by_name(
        self,
        name: str,
    ) -> list[str]:
        self.query_count += 1
        return list(
            self.query.find_nodes_by_name(name)
        )

    def has_node(
        self,
        node_id: str,
    ) -> bool:
        self.query_count += 1
        return bool(
            self.query.has_node(node_id)
        )

    def ready(self) -> bool:
        return (
            self.graph is not None
            and self.query is not None
            and self.builder is not None
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "components": {
                "graph": type(
                    self.graph
                ).__name__,
                "query": type(
                    self.query
                ).__name__,
                "builder": type(
                    self.builder
                ).__name__,
            },
            "metrics": {
                "queries": self.query_count,
                "builds": self.build_count,
                "nodes": len(
                    self.graph.nodes
                ),
                "relations": len(
                    self.graph.relations
                ),
            },
        }

__all__ = [
    "GraphProvider",
]
