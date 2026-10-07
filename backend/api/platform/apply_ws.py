"""WS 端点：/ws/platform/apply/{task_id} —— 代码应用实时进度流。

与 finetune.deploy_ws 的区别（不重复职责）：
    - deploy_ws  订阅 DeployHub（模型部署领域）
    - apply_ws   订阅 ApplyHub （代码应用领域）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import json

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.platform.apply_hub import get_apply_hub

router = APIRouter()

_TERMINAL = {"succeeded", "failed", "cancelled"}


@router.websocket("/ws/platform/apply/{task_id}")
async def apply_progress_ws(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    hub = get_apply_hub()
    task = hub.get(task_id)

    if task is None:
        try:
            await websocket.send_text(json.dumps({
                "type": "error", "message": f"task not found: {task_id}",
            }))
            await websocket.close()
        except Exception as e:
            swallow("api.platform.apply_ws:36", e, level="warn")
        return

    # 回放已有事件
    for ev in list(task.get("events", [])):
        try:
            await websocket.send_text(json.dumps(ev, ensure_ascii=False))
        except Exception:
            return

    # 已结束 → 直接关闭
    if task.get("status") in _TERMINAL:
        try:
            await websocket.send_text(json.dumps({
                "type": "_end", "status": task["status"]}))
            await websocket.close()
        except Exception as e:
            swallow("api.platform.apply_ws:53", e, level="warn")
        return

    q = hub.subscribe(task_id)
    try:
        while True:
            ev = await asyncio.wait_for(q.get(), timeout=600)
            await websocket.send_text(json.dumps(ev, ensure_ascii=False))
            if ev.get("type") == "_end":
                break
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        swallow("api.platform.apply_ws:68", e, level="warn")
    finally:
        hub.unsubscribe(task_id, q)
        try:
            await websocket.close()
        except Exception as e:
            swallow("api.platform.apply_ws:74", e, level="warn")


__all__ = ["router"]
