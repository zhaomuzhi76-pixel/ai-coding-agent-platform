"""WS 端点：/ws/finetune/deploy/{task_id} —— 部署实时进度流。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import json

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.finetune.deploy.deploy_hub import get_deploy_hub

router = APIRouter()

_TERMINAL = {"succeeded", "failed", "cancelled"}


@router.websocket("/ws/finetune/deploy/{task_id}")
async def deploy_progress_ws(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    hub = get_deploy_hub()
    task = hub.get(task_id)

    if task is None:
        await websocket.send_text(json.dumps({
            "type": "error", "message": f"task not found: {task_id}",
        }))
        try:
            await websocket.close()
        except Exception as e:
            swallow("api.finetune.deploy_ws:31", e, level="warn")
        return

    # 回放已有事件
    for ev in list(task.get("events", [])):
        try:
            await websocket.send_text(json.dumps(ev, ensure_ascii=False))
        except Exception:
            return

    # 若任务已结束，直接关闭
    if task.get("status") in _TERMINAL:
        try:
            await websocket.send_text(json.dumps({
                "type": "_end", "status": task["status"]}))
            await websocket.close()
        except Exception as e:
            swallow("api.finetune.deploy_ws:48", e, level="warn")
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
        swallow("api.finetune.deploy_ws:63", e, level="warn")
    finally:
        hub.unsubscribe(task_id, q)
        try:
            await websocket.close()
        except Exception as e:
            swallow("api.finetune.deploy_ws:69", e, level="warn")


__all__ = ["router"]
