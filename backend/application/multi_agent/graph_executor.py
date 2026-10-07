"""L3 · Graph Executor（DAG 节点编排 · 单一职责）。

职责：
  · Graph：节点 + 依赖（DAG）
  · GraphExecutor：拓扑执行，按依赖顺序
  · 节点 = (node_id, agent_id, task, deps)
  · 执行时通过 MessageBus 派发到 Agent

不做：路由决策（TaskRouter 管）、实际 Agent 执行。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.application.multi_agent.message_bus import (
    MessageBus, get_default_bus,
)


@dataclass(frozen=True)
class GraphNode:
    """DAG 节点。"""
    node_id: str
    agent_id: str
    task: str
    deps: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Graph:
    """DAG 图（拓扑顺序保证）。"""
    graph_id: str
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def add(self, node: GraphNode) -> None:
        if not node.node_id:
            raise ValueError("node_id required")
        self.nodes[node.node_id] = node

    def topo_order(self) -> List[GraphNode]:
        """Kahn 拓扑排序 · 环则抛异常。"""
        indeg: Dict[str, int] = {nid: 0 for nid in self.nodes}
        adj: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        for nid, node in self.nodes.items():
            for d in node.deps:
                if d not in self.nodes:
                    raise ValueError("missing dep: {}".format(d))
                adj[d].append(nid)
                indeg[nid] += 1
        queue = [nid for nid, d in indeg.items() if d == 0]
        out: List[GraphNode] = []
        while queue:
            nid = queue.pop(0)
            out.append(self.nodes[nid])
            for m in adj[nid]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)
        if len(out) != len(self.nodes):
            raise ValueError("cycle detected in graph {}".format(self.graph_id))
        return out

    def size(self) -> int:
        return len(self.nodes)


class GraphExecutor:
    """DAG 执行器（派发到 Agent）。"""

    def __init__(self, bus: Optional[MessageBus] = None) -> None:
        self._bus = bus or get_default_bus()

    def execute(self, graph: Graph) -> Dict[str, Any]:
        """按拓扑顺序派发每个节点到对应 Agent。返回执行报告。"""
        order = graph.topo_order()
        sent: List[Dict[str, Any]] = []
        for node in order:
            self._bus.emit_to_agent(
                node.agent_id,
                topic="graph.node.dispatch",
                payload={
                    "graph_id": graph.graph_id,
                    "node_id": node.node_id,
                    "task": node.task,
                    "deps": list(node.deps),
                },
                sender="graph_executor",
            )
            sent.append({"node_id": node.node_id,
                         "agent_id": node.agent_id,
                         "task": node.task})
        return {
            "graph_id": graph.graph_id,
            "total": len(order),
            "dispatched": sent,
        }


def make_graph(graph_id: str, nodes: List[GraphNode]) -> Graph:
    g = Graph(graph_id=graph_id)
    for n in nodes:
        g.add(n)
    return g


__all__ = ["GraphNode", "Graph", "GraphExecutor", "make_graph"]
