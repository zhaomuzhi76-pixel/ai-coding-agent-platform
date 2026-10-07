"""Mixin 2 of PlatformBackedCoordinator."""
from __future__ import annotations
from .part1 import (Any, Dict,)  # noqa: F401
class _Mixin2:
    async def _send(
        self, websocket, transport_session_id, model, body,
    ) -> None:
        # 工业级兜底：WS 已断时直接跳过（不抛异常）
        try:
            from starlette.websockets import WebSocketState
            state = getattr(
                websocket, "client_state", None,
            )
            if state is not None and state != WebSocketState.CONNECTED:
                return
        except Exception as e:
            print(
                "[ws-send] client_state check failed: "
                + type(e).__name__ + ": " + str(e),
                flush=True,
            )

        try:
            await self.sender.send_result(
                websocket, transport_session_id, model, body,
            )
        except Exception as e:
            # 工业级：任何发送失败都暴露出来（否则客户端收不到帧无法定位）
            print(
                "[ws-send] send_result failed: "
                + type(e).__name__ + ": " + str(e),
                flush=True,
            )
            try:
                import traceback
                traceback.print_exc()
            except Exception:  # silent-ok
                pass

    async def _fail(
        self, websocket, transport_session_id, model, reason,
    ) -> None:
        await self._send(
            websocket, transport_session_id, model,
            {"success": False, "error": reason},
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "executions": self.execution_count,
            "failures": self.failure_count,
        }
