"""WSHeartbeat: WebSocket 心跳保活。

Owns: 周期性 ping / 心跳任务生命周期
Not:  消息路由 / 连接管理 / 异常策略
"""
from __future__ import annotations
import asyncio, contextlib
from typing import Any


class WSHeartbeat:
    VERSION = "1.0"

    def __init__(self, interval_sec: float = 25.0) -> None:
        if interval_sec < 0:
            raise ValueError("interval_sec must be >= 0")
        # 0 = disabled（协议层心跳由 uvicorn ws_ping_interval 负责）
        self.interval_sec = interval_sec
        self.sent = 0

    async def run(self, websocket: Any) -> None:
        send_json = getattr(websocket, "send_json", None)
        if not callable(send_json):
            raise TypeError("websocket send_json required")
        try:
            while True:
                await asyncio.sleep(self.interval_sec)
                with contextlib.suppress(Exception):
                    await send_json({"type": "ping"})
                    self.sent += 1
        except asyncio.CancelledError:
            return

    def ready(self) -> bool:
        # interval=0 是合法状态（禁用），>=0 都 ready
        return self.interval_sec >= 0

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION,
                "interval_sec": self.interval_sec, "sent": self.sent}


__all__ = ["WSHeartbeat"]
