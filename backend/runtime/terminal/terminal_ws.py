"""WebSocket 端点：/ws/terminal —— 桥接前端 xterm 与本地 PTY。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import json

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from .pty_session import PtySession

router = APIRouter()


@router.websocket("/ws/terminal")
async def terminal_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    output_queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def on_output(data: bytes) -> None:
        # 从 reader 回调（同一 loop）投递
        try:
            loop.call_soon_threadsafe(output_queue.put_nowait, data)
        except RuntimeError:
            pass

    session = PtySession(on_output=on_output)
    try:
        await session.start()
    except Exception as exc:
        await websocket.send_text(f"\r\n\x1b[31m[pty start failed] {exc}\x1b[0m\r\n")
        await websocket.close()
        return

    async def pump_output() -> None:
        try:
            while True:
                chunk = await output_queue.get()
                await websocket.send_bytes(chunk)
        except Exception as e:
            swallow("runtime.terminal.terminal_ws:44", e, level="warn")

    pump_task = asyncio.create_task(pump_output())

    try:
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            text = msg.get("text")
            data = msg.get("bytes")
            if data is not None:
                session.write(data)
            elif text is not None:
                # 控制消息或普通文本
                if text.startswith("{"):
                    try:
                        obj = json.loads(text)
                        if obj.get("type") == "resize":
                            session.resize(int(obj["cols"]), int(obj["rows"]))
                            continue
                    except Exception as e:
                        swallow("runtime.terminal.terminal_ws:66", e, level="warn")
                session.write(text.encode("utf-8"))
    except WebSocketDisconnect:
        pass
    finally:
        pump_task.cancel()
        session.close()
        try:
            await websocket.close()
        except Exception as e:
            swallow("runtime.terminal.terminal_ws:76", e, level="warn")
