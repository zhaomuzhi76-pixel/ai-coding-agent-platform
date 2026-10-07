from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    FILE = "file"
    SYMBOL = "symbol"


class RelationType(str, Enum):
    IMPORT = "import"
    CALL = "call"
    REFERENCE = "reference"


@dataclass
class GraphNode:
    node_id: str
    name: str
    node_type: NodeType
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node_id required")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("node name required")
        if not isinstance(self.node_type, NodeType):
            raise TypeError("invalid node type")

    def ready(self) -> bool:
        return bool(
            self.node_id
            and self.name
            and isinstance(self.node_type, NodeType)
            and isinstance(self.metadata, dict)
        )


@dataclass
class GraphRelation:
    source: str
    target: str
    relation_type: RelationType

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("relation source required")
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError("relation target required")
        if not isinstance(self.relation_type, RelationType):
            raise TypeError("invalid relation type")

    def ready(self) -> bool:
        return bool(
            self.source
            and self.target
            and isinstance(self.relation_type, RelationType)
        )


@dataclass
class CodeGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    relations: list[GraphRelation] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        if not isinstance(node, GraphNode):
            raise TypeError("node must GraphNode")
        self.nodes[node.node_id] = node

    def add_relation(self, relation: GraphRelation) -> None:
        if not isinstance(relation, GraphRelation):
            raise TypeError("relation must GraphRelation")
        self.relations.append(relation)

    def ready(self) -> bool:
        return (
            isinstance(self.nodes, dict)
            and isinstance(self.relations, list)
            and all(node.ready() for node in self.nodes.values())
            and all(relation.ready() for relation in self.relations)
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "nodes": len(self.nodes),
            "relations": len(self.relations),
            "ready": self.ready(),
        }


__all__ = [
    "NodeType",
    "RelationType",
    "GraphNode",
    "GraphRelation",
    "CodeGraph",
]
