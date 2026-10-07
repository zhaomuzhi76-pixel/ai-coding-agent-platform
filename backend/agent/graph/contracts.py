from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GraphBuildItemProtocol(Protocol):
    node_id: str
    node_type: str
    executor_type: str
    description: str
    depends_on: list[str]
    parameters: dict[str, Any]
    metadata: dict[str, Any]


@runtime_checkable
class GraphNodeProtocol(Protocol):
    node_id: str
    node_type: str
    executor_type: str
    depends_on: list[str]

    def is_finished(self) -> bool:
        ...


@runtime_checkable
class GraphProtocol(Protocol):
    def add_node(
        self,
        node: GraphNodeProtocol,
    ) -> None:
        ...

    def get_node(
        self,
        node_id: str,
    ) -> GraphNodeProtocol | None:
        ...

    def all_nodes(
        self,
    ) -> list[GraphNodeProtocol]:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "GraphBuildItemProtocol",
    "GraphNodeProtocol",
    "GraphProtocol",
]
