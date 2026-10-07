"""Graph Plan Service · 独立新入口（单一职责）。

输入：TaskPlan（已构造好）
输出：执行报告（派发清单 + 收件箱快照）

职责：
  · 把 plan 转为 DAG 并派发到 MessageBus
  · 与编排层解耦（互不依赖）
  · env RAG_MA_GRAPH_PLAN=1 启用

不做：planning、LLM 执行、状态持久化。
"""
from __future__ import annotations
import os
from typing import Any, Dict, Optional

from backend.application.multi_agent.message_bus import (
    MessageBus, get_default_bus,
)
from backend.application.multi_agent.graph_executor import GraphExecutor
from backend.application.multi_agent.plan_graph_adapter import plan_to_graph


def is_enabled() -> bool:
    v = os.environ.get("RAG_MA_GRAPH_PLAN", "0").strip().lower()
    return v in ("1", "true", "yes", "on")


def execute_plan(plan: Any,
                 bus: Optional[MessageBus] = None) -> Dict[str, Any]:
    """TaskPlan → Graph → GraphExecutor.execute()。"""
    if plan is None:
        return {"ok": False, "error": "plan is None"}
    graph = plan_to_graph(plan)
    b = bus or get_default_bus()
    ex = GraphExecutor(bus=b)
    try:
        report = ex.execute(graph)
    except Exception as e:
        return {"ok": False,
                "error": "{}: {}".format(type(e).__name__, str(e)),
                "graph_id": graph.graph_id}

    inboxes: Dict[str, list] = {}
    for node in graph.topo_order():
        aid = node.agent_id
        if aid in inboxes:
            continue
        inboxes[aid] = [m.topic for m in b.peek(aid)][-5:]

    return {
        "ok": True,
        "graph_id": graph.graph_id,
        "total": report["total"],
        "dispatched": report["dispatched"],
        "inboxes": inboxes,
    }


def snapshot() -> Dict[str, Any]:
    return {"enabled": is_enabled(),
            "features": ["plan_to_graph", "graph_dispatch", "inbox_peek"]}


__all__ = ["is_enabled", "execute_plan", "snapshot"]
