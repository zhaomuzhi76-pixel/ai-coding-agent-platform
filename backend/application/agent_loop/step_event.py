"""把 agent_loop 的一步包装成 RuntimeEventV2（前端契约）。

工业级契约：
  - 复用 RuntimeEvent 的 v2 序列化（唯一来源）
  - type 必须在前端 RuntimeEventType 白名单内
  - 每步带 remaining / thought / action / args / observation

调用方：ws_platform_coordinator._emit_step
"""
from __future__ import annotations

from typing import Any

from backend.core.events.types import CoreEventType
from backend.runtime.events.event import RuntimeEvent

_SOURCE = "agent_loop.step"

# 前端 RuntimeEventType 允许：
#   node_start / node_finish / node_failed / tool_call / tool_result
# 每步 agent_loop：
#   - 有 action 且成功 → tool_call
#   - 有 action 但被防重复拦截 → tool_result（带 repeated=true）
#   - done → node_finish


def _pick_event_type(entry: dict[str, Any]) -> str:
    # [PT] 写操作挂起 → 独立类型
    if str(entry.get("type", "")).strip() == "pending_edit":
        candidate = "pending_edit"
    elif entry.get("done") is True:
        candidate = "node_finish"
    elif entry.get("repeated"):
        candidate = "tool_result"
    else:
        candidate = "tool_call"

    # 校验：CoreEventType 必须接受
    if CoreEventType.contains(candidate):
        return candidate
    # 白名单未注册 pending_edit → 降级 tool_call（保留 data.pending）
    if candidate == "pending_edit":
        return "tool_call"
    return "node_finish"


def to_runtime_event_v2(
    entry: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    """把 agent_loop 的一步转成 RuntimeEventV2 完整字典。"""
    step_no = int(entry.get("step", 0))
    node_id = f"agent-loop-step-{step_no}"

    data = {
        "step": step_no,
        "thought": entry.get("thought", ""),
        "action": entry.get("action", ""),
        "args": entry.get("args", {}),
        "observation": entry.get("observation", ""),
        "remaining": entry.get("remaining", 0),
        "repeated": bool(entry.get("repeated", False)),
        "done": bool(entry.get("done", False)),
        "session_id": session_id,
    }
    # 审批字段透传（pending / rejected / type）
    for key in ("pending", "rejected", "type"):
        if key in entry:
            data[key] = entry[key]

    event = RuntimeEvent.create(
        _pick_event_type(entry),
        data=data,
        source=_SOURCE,
        node_id=node_id,
    )

    # dump() 补齐前端需要的 version + responsibility
    return event.dump()


__all__ = ["to_runtime_event_v2"]
