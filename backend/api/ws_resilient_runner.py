"""WSResilientRunner: 心跳 + 异常策略的组合运行器。

Owns:
    - 组合 WSHeartbeat + WSExceptionPolicy
    - 提供"任何 recoverable 异常不断连"的消息循环

Not:
    - 消息解码（外部注入）
    - 业务处理（外部注入）
    - WS 发送实现（外部注入）
"""
from __future__ import annotations
import asyncio
from typing import Any, Awaitable, Callable

from backend.api.ws_exception_policy import WSExceptionPolicy
from backend.api.ws_heartbeat import WSHeartbeat


class WSResilientRunner:
    VERSION = "1.0"

    def __init__(
        self,
        *,
        heartbeat_interval_sec: float = 25.0,
        policy: WSExceptionPolicy | None = None,
        heartbeat: WSHeartbeat | None = None,
        max_consecutive_recoverable: int = 5,
    ) -> None:
        self.policy = policy or WSExceptionPolicy()
        self.heartbeat = heartbeat or WSHeartbeat(heartbeat_interval_sec)
        self.max_consecutive_recoverable = max_consecutive_recoverable
        self.handled = 0
        self.recovered = 0

    async def run(
        self,
        *,
        receive: Callable[[], Awaitable[dict]],
        handle: Callable[[dict], Awaitable[None]],
        send_error: Callable[[str], Awaitable[None]],
        on_fatal: Callable[[BaseException], None] | None = None,
        websocket: Any = None,
    ) -> None:
        hb_task = None
        if websocket is not None and self.heartbeat.interval_sec > 0:
            hb_task = asyncio.create_task(self.heartbeat.run(websocket))
        consecutive = 0
        try:
            while True:
                try:
                    payload = await receive()
                    consecutive = 0
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    if not self.policy.should_continue(exc):
                        if on_fatal: on_fatal(exc)
                        raise
                    consecutive += 1
                    self.recovered += 1
                    if consecutive >= self.max_consecutive_recoverable:
                        # 工业级：达到上限优雅退出（不 raise 到进程级）
                        print(
                            '[ws_resilient] consecutive recoverable limit '
                            + str(consecutive) + ' reached, graceful exit',
                            flush=True,
                        )
                        break
                    await send_error(self.policy.format_error(exc))
                    continue

                try:
                    await handle(payload)
                    self.handled += 1
                except Exception as exc:
                    if not self.policy.should_continue(exc):
                        if on_fatal: on_fatal(exc)
                        raise
                    import traceback; traceback.print_exc()
                    self.recovered += 1
                    await send_error(self.policy.format_error(exc))
                    continue
        finally:
            if hb_task is not None:
                hb_task.cancel()
                try: await hb_task
                except (asyncio.CancelledError, Exception): pass

    def ready(self) -> bool:
        return self.policy.ready() and self.heartbeat.ready()

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION,
                "handled": self.handled, "recovered": self.recovered,
                "heartbeat": self.heartbeat.dump(),
                "policy": self.policy.dump()}


__all__ = ["WSResilientRunner"]
