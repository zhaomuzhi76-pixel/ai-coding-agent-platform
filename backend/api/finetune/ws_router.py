"""WS 端点：/ws/finetune/jobs —— JobEvent 实时流。

职责：
    - WebSocket 握手 / 心跳 / 断连
    - 订阅 JobManager 的事件多播
    - JSON 编解码

不负责：
    - 事件产生（job/event.py + runner.py 管）
    - 多播机制（job/manager.py 的 subscribe 管）
    - 持久化（job/store.py 管）
    - 前端重连（前端 ResilientSocket 管）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import json

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.finetune.job.event import JobEvent
from backend.finetune.job.manager import get_job_manager

router = APIRouter()

_QUEUE_MAXSIZE = 1000
_PING_TEXT = "ping"
_PONG_JSON = "{\"type\":\"pong\"}"


@router.websocket("/ws/finetune/jobs")
async def finetune_jobs_ws(websocket: WebSocket) -> None:
    await websocket.accept()

    job_filter = websocket.query_params.get("job_id") or None
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)

    def _on_event(event: JobEvent) -> None:
        if job_filter is not None and event.payload.get("job_id") != job_filter:
            return
        try:
            queue.put_nowait(event.to_dict())
        except asyncio.QueueFull:
            # 慢消费者保护：丢最旧
            try:
                _ = queue.get_nowait()
                queue.put_nowait(event.to_dict())
            except Exception as e:
                swallow("api.finetune.ws_router:51", e, level="warn")

    manager = get_job_manager()
    unsubscribe = manager.subscribe(_on_event)

    async def _pump() -> None:
        try:
            while True:
                ev = await queue.get()
                await websocket.send_text(json.dumps(ev, ensure_ascii=False))
        except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
            pass
        except Exception as e:
            swallow("api.finetune.ws_router:64", e, level="warn")

    pump_task = asyncio.create_task(_pump())

    try:
        while True:
            msg = await websocket.receive()
            mtype = msg.get("type")
            if mtype == "websocket.disconnect":
                break
            text = msg.get("text")
            if text == _PING_TEXT:
                await websocket.send_text(_PONG_JSON)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        swallow("api.finetune.ws_router:80", e, level="warn")
    finally:
        pump_task.cancel()
        try:
            await pump_task
        except (asyncio.CancelledError, Exception):
            pass
        try:
            unsubscribe()
        except Exception as e:
            swallow("api.finetune.ws_router:90", e, level="warn")


__all__ = ["router"]
