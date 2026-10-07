"""Tree WS 端点：/ws/tree。

契约：
    - 多连接订阅同一 root → 共享 1 个 TreeWatcher（引用计数）
    - subscribe → 加入 registry；unsubscribe / 断开 → 退出
    - 每连接独立 session_id

不负责：
    - 文件树 HTTP API
    - 文件监控实现（tree/watch 管）
    - 协议构造（ws_tree_protocol 管）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import uuid

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.api import ws_tree_protocol as proto
from backend.workspace.tree.watch.event_router import get_registry

router = APIRouter()

PATH = "/ws/tree"
WATCH_INTERVAL_SEC = 2.0


async def _safe_send(ws: WebSocket, payload: dict) -> bool:
    try:
        await ws.send_json(payload)
        return True
    except Exception:
        return False


@router.websocket(PATH)
async def ws_tree(websocket: WebSocket):
    await websocket.accept()
    session_id = "ws-tree-" + uuid.uuid4().hex[:8]

    project_id = ""
    unsubscribe = None

    await _safe_send(websocket, proto.make_tree_ready(session_id))

    async def _emit(events) -> None:
        if not events:
            return
        payload = proto.make_tree_changed(
            project_id, session_id, [e.to_dict() for e in events],
        )
        await _safe_send(websocket, payload)

    async def _drop_subscription() -> None:
        nonlocal unsubscribe, project_id
        if unsubscribe is not None:
            try:
                await unsubscribe()
            except Exception as e:
                swallow("api.ws_tree:62", e, level="warn")
            unsubscribe = None
        project_id = ""

    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            try:
                action, data = proto.parse_tree_action(raw)
            except proto.TreeProtocolError as exc:
                await _safe_send(
                    websocket, proto.make_tree_error(session_id, str(exc)),
                )
                continue

            if action == proto.ACTION_PING:
                await _safe_send(websocket, proto.make_tree_pong(session_id))
                continue

            if action == proto.ACTION_UNSUBSCRIBE:
                await _drop_subscription()
                continue

            if action == proto.ACTION_SUBSCRIBE:
                await _drop_subscription()

                pid = data["project_id"]
                root_str = data["workspace_root"]
                from pathlib import Path as _Path
                root = _Path(root_str)
                if not root.exists() or not root.is_dir():
                    await _safe_send(
                        websocket,
                        proto.make_tree_error(
                            session_id, "workspace_root not a directory",
                        ),
                    )
                    continue
                project_id = pid
                registry = get_registry()
                try:
                    unsubscribe = await registry.subscribe_root(
                        root, _emit, interval_sec=WATCH_INTERVAL_SEC,
                    )
                except Exception as exc:
                    await _safe_send(
                        websocket,
                        proto.make_tree_error(
                            session_id,
                            "subscribe failed: " + type(exc).__name__,
                        ),
                    )
                    project_id = ""
                    continue
                await _safe_send(
                    websocket,
                    proto.make_tree_subscribed(pid, session_id),
                )
    finally:
        await _drop_subscription()


def register_ws_tree(app) -> None:
    add_route = getattr(app, "add_api_websocket_route", None)
    if not callable(add_route):
        raise TypeError("app must expose add_api_websocket_route()")
    existing = {getattr(r, "path", None) for r in getattr(app.router, "routes", ())}
    if PATH in existing:
        return
    add_route(PATH, ws_tree, name="ws_tree")


__all__ = ["router", "ws_tree", "register_ws_tree", "PATH"]
