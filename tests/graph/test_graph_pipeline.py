from __future__ import annotations

from dataclasses import dataclass, field

from backend.agent.graph.graph_builder import GraphBuilder
from backend.agent.graph.graph_validator import GraphValidator


@dataclass
class GraphItem:
    node_id: str
    executor_type: str
    description: str
    node_type: str = "task"
    depends_on: list[str] = field(default_factory=list)
    parameters: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)


def test_graph_build_and_validate() -> None:
    items = [
        GraphItem(
            node_id="node_1",
            executor_type="file_read",
            description="read self",
            parameters={
                "path": "backend/agent/graph/node.py",
            },
        ),
        GraphItem(
            node_id="node_2",
            executor_type="summary",
            description="summarize",
            depends_on=["node_1"],
        ),
    ]

    graph = GraphBuilder().build(items)

    assert graph.ready()
    assert graph.node_count() == 2
    assert graph.get_node("node_1") is not None
    assert graph.get_node("node_2") is not None

    validation = GraphValidator().validate(graph)

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_graph_rejects_missing_dependency() -> None:
    graph = GraphBuilder().build(
        [
            GraphItem(
                node_id="node_1",
                executor_type="file_read",
                description="read",
                depends_on=["missing"],
            )
        ]
    )

    validation = GraphValidator().validate(graph)

    assert validation["valid"] is False
    assert "missing dependency:missing for node:node_1" in (
        validation["errors"]
    )


def test_graph_rejects_cycle() -> None:
    graph = GraphBuilder().build(
        [
            GraphItem(
                node_id="node_1",
                executor_type="task",
                description="first",
                depends_on=["node_2"],
            ),
            GraphItem(
                node_id="node_2",
                executor_type="task",
                description="second",
                depends_on=["node_1"],
            ),
        ]
    )

    validation = GraphValidator().validate(graph)

    assert validation["valid"] is False
    assert "cycle detected" in validation["errors"]
