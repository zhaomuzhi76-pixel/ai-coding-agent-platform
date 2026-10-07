from __future__ import annotations

from backend.codebase.graph.model import (
    CodeGraph,
    RelationType,
)


class CodeGraphQuery:
    """
    Query boundary for the code graph.

    Owns graph traversal and lookup semantics.
    Does not mutate graph state.
    """

    def __init__(
        self,
        graph: CodeGraph,
    ) -> None:
        if graph is None:
            raise ValueError("graph required")
        self.graph = graph

    def find_dependents(
        self,
        node_id: str,
    ) -> list[str]:
        return [
            relation.source
            for relation in self.graph.relations
            if (
                relation.target == node_id
                and relation.relation_type
                is RelationType.IMPORT
            )
        ]

    def find_symbols(
        self,
        file_id: str,
    ) -> list[str]:
        return [
            relation.target
            for relation in self.graph.relations
            if (
                relation.source == file_id
                and relation.relation_type
                is RelationType.REFERENCE
            )
        ]

    def find_related(
        self,
        node_id: str,
    ) -> list[str]:
        related = set()

        for relation in self.graph.relations:
            if (
                relation.target == node_id
                and relation.relation_type
                in (
                    RelationType.IMPORT,
                    RelationType.CALL,
                    RelationType.REFERENCE,
                )
            ):
                related.add(relation.source)

            if (
                relation.source == node_id
                and relation.relation_type
                in (
                    RelationType.CALL,
                    RelationType.REFERENCE,
                )
            ):
                related.add(relation.target)

        return sorted(related)

    def has_node(
        self,
        node_id: str,
    ) -> bool:
        return node_id in self.graph.nodes

    def find_nodes_by_name(
        self,
        name: str,
    ) -> list[str]:
        return sorted(
            node_id
            for node_id, node in self.graph.nodes.items()
            if node.name == name
        )


__all__ = [
    "CodeGraphQuery",
]
