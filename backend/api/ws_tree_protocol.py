"""TreeWS 协议：消息构造 + 解析。

契约：
  - 客户端 action：subscribe / unsubscribe / ping
  - 服务端 type：ready / subscribed / tree_changed / pong / error
  - subscribe 必须带 project_id + workspace_root
  - 所有消息含 session_id（客户端 action 除外）

不负责：
  - 连接管理（ws_tree.py 管）
  - 文件监控（tree/watch 管）
  - 事件传输
"""
from __future__ import annotations

from typing import Any


ACTION_SUBSCRIBE = "subscribe"
ACTION_UNSUBSCRIBE = "unsubscribe"
ACTION_PING = "ping"

TYPE_READY = "ready"
TYPE_SUBSCRIBED = "subscribed"
TYPE_TREE_CHANGED = "tree_changed"
TYPE_PONG = "pong"
TYPE_ERROR = "error"

_ALL_ACTIONS = frozenset({ACTION_SUBSCRIBE, ACTION_UNSUBSCRIBE, ACTION_PING})


class TreeProtocolError(ValueError):
    """WS tree 协议违规。"""


def make_tree_ready(session_id: str) -> dict[str, Any]:
    return {"type": TYPE_READY, "session_id": str(session_id)}


def make_tree_subscribed(project_id: str, session_id: str) -> dict[str, Any]:
    return {
        "type": TYPE_SUBSCRIBED,
        "session_id": str(session_id),
        "project_id": str(project_id),
    }


def make_tree_changed(
    project_id: str,
    session_id: str,
    events: list[dict],
) -> dict[str, Any]:
    if not isinstance(events, list):
        raise TreeProtocolError("events must be list")
    return {
        "type": TYPE_TREE_CHANGED,
        "session_id": str(session_id),
        "project_id": str(project_id),
        "events": events,
    }


def make_tree_pong(session_id: str) -> dict[str, Any]:
    return {"type": TYPE_PONG, "session_id": str(session_id)}


def make_tree_error(session_id: str, reason: str) -> dict[str, Any]:
    return {
        "type": TYPE_ERROR,
        "session_id": str(session_id),
        "reason": str(reason),
    }


def parse_tree_action(payload: Any) -> tuple[str, dict[str, Any]]:
    """返回 (action, data)。失败抛 TreeProtocolError。"""
    if not isinstance(payload, dict):
        raise TreeProtocolError("payload must be dict")
    action = str(payload.get("action", "")).strip()
    if action not in _ALL_ACTIONS:
        raise TreeProtocolError("unknown action: " + repr(action))
    if action == ACTION_SUBSCRIBE:
        pid = str(payload.get("project_id", "")).strip()
        root = str(payload.get("workspace_root", "")).strip()
        if not pid:
            raise TreeProtocolError("project_id required")
        if not root:
            raise TreeProtocolError("workspace_root required")
        return action, {"project_id": pid, "workspace_root": root}
    return action, {}


__all__ = [
    "TreeProtocolError",
    "ACTION_SUBSCRIBE", "ACTION_UNSUBSCRIBE", "ACTION_PING",
    "TYPE_READY", "TYPE_SUBSCRIBED", "TYPE_TREE_CHANGED",
    "TYPE_PONG", "TYPE_ERROR",
    "make_tree_ready", "make_tree_subscribed", "make_tree_changed",
    "make_tree_pong", "make_tree_error", "parse_tree_action",
]
