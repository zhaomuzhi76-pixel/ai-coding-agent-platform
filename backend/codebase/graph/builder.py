from __future__ import annotations

from typing import Any

from backend.codebase.graph.model import (
    CodeGraph,
    GraphNode,
    GraphRelation,
    NodeType,
    RelationType,
)


class CodeGraphBuilder:
    VERSION = "1.0"

    def build(
        self,
        files: list[dict[str, Any]],
    ) -> CodeGraph:
        if not isinstance(files, list):
            raise TypeError("files must list")

        graph = CodeGraph()

        for item in files:
            if not isinstance(item, dict):
                raise TypeError("graph file item must dict")
            self._add_file(graph, item)

        if not graph.ready():
            raise RuntimeError("code graph build unavailable")

        return graph

    def _add_file(
        self,
        graph: CodeGraph,
        item: dict[str, Any],
    ) -> None:
        file_id = item.get("path")
        if not isinstance(file_id, str) or not file_id.strip():
            raise ValueError("graph file path required")

        graph.add_node(
            GraphNode(
                node_id=file_id,
                name=file_id,
                node_type=NodeType.FILE,
            )
        )

        symbols = item.get("symbols", [])
        if not isinstance(symbols, list):
            raise TypeError("symbols must list")

        for symbol in symbols:
            self._add_symbol(
                graph,
                file_id,
                symbol,
            )

        imports = item.get("imports", [])
        if not isinstance(imports, list):
            raise TypeError("imports must list")

        for target in imports:
            if not isinstance(target, str) or not target.strip():
                raise ValueError("import target required")
            graph.add_relation(
                GraphRelation(
                    source=file_id,
                    target=target,
                    relation_type=RelationType.IMPORT,
                )
            )

    def _add_symbol(
        self,
        graph: CodeGraph,
        file_id: str,
        symbol: str,
    ) -> None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol required")

        symbol_id = f"{file_id}:{symbol}"

        graph.add_node(
            GraphNode(
                node_id=symbol_id,
                name=symbol,
                node_type=NodeType.SYMBOL,
            )
        )

        graph.add_relation(
            GraphRelation(
                source=file_id,
                target=symbol_id,
                relation_type=RelationType.REFERENCE,
            )
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "CodeGraphBuilder",
]
