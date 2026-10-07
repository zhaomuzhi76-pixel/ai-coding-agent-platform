"""TaskPlan → Graph 适配器（防御式 · 单一职责）。

真实 PlanStep 字段（项目实测）：
  node_id / executor_type / description / node_type
  / depends_on / parameters / metadata

职责：
  · plan_to_graph(plan) -> Graph
  · 无 depends_on 时 → 顺序链 fallback

env: 无（纯函数）
"""
from __future__ import annotations
from typing import Any, List, Tuple

from backend.application.multi_agent.graph_executor import (
    Graph, GraphNode, make_graph,
)


def _get_first(obj: Any, *names: str, default: Any = None) -> Any:
    """按顺序取第一个存在的非空属性（防御式）。"""
    for n in names:
        v = getattr(obj, n, None)
        if v is not None and v != "":
            return v
    return default


def _extract_step_info(step: Any, idx: int) -> Tuple[str, str, str, Tuple[str, ...]]:
    """从任意 PlanStep 提取 (node_id, agent_id, task, deps)。

    字段优先（真实 > 兼容）：
      node_id      : node_id > step_id > id
      agent_id     : executor_type > agent_id > agent > role
      task         : description > task > action > prompt
      deps         : depends_on > deps > after
    """
    sid = str(_get_first(step, "node_id", "step_id", "id",
                          default="step-{}".format(idx)))
    aid = str(_get_first(step, "executor_type", "agent_id", "agent",
                          "role", "owner", default="chat"))
    task = str(_get_first(step, "description", "task", "action",
                           "goal", "prompt", default=""))
    deps_raw = _get_first(step, "depends_on", "deps", "after", default=())
    try:
        deps = tuple(str(d) for d in deps_raw if d)
    except TypeError:
        deps = ()
    return sid, aid, task, deps


def plan_to_graph(plan: Any, chain_fallback: bool = True) -> Graph:
    """TaskPlan → Graph。chain_fallback: 无 deps 时串顺序链。"""
    if plan is None:
        return Graph(graph_id="empty")

    plan_id = str(_get_first(plan, "plan_id", "id", default="plan"))
    goal = str(_get_first(plan, "goal", default="") or "")
    steps = list(getattr(plan, "steps", None) or ())
    if not steps:
        return Graph(graph_id=plan_id)

    nodes: List[GraphNode] = []
    prev_id: str = ""
    for i, s in enumerate(steps):
        sid, aid, task, deps = _extract_step_info(s, i)
        if not deps and chain_fallback and prev_id:
            deps = (prev_id,)
        nodes.append(GraphNode(
            node_id=sid, agent_id=aid, task=task or goal, deps=deps,
            metadata={"source": "plan", "index": i},
        ))
        prev_id = sid
    return make_graph(plan_id, nodes)


def snapshot(plan: Any) -> dict:
    if plan is None:
        return {"plan": None}
    steps = list(getattr(plan, "steps", None) or ())
    infos = [_extract_step_info(s, i) for i, s in enumerate(steps)]
    return {
        "plan_id": str(_get_first(plan, "plan_id", "id", default="?")),
        "goal": str(_get_first(plan, "goal", default="") or "")[:60],
        "steps": len(steps),
        "step_infos": [
            {"id": i, "agent": a, "task": t[:40], "deps": list(d)}
            for i, a, t, d in infos
        ],
    }


__all__ = ["plan_to_graph", "snapshot"]
