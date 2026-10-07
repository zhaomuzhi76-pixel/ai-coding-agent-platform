"""WSAgentHandler: WS 请求 → PlatformBackedCoordinator。

只做协议适配：payload 校验 + 委托给 coordinator。
执行逻辑在 platform。
"""
from __future__ import annotations

from typing import Any

from fastapi import WebSocket


class WSAgentHandler:
    VERSION = "5.0"

    def __init__(self, coordinator: Any) -> None:
        if coordinator is None:
            raise ValueError("coordinator required")
        self.coordinator = coordinator
        self.handle_count = 0

    async def handle(
        self,
        websocket: WebSocket,
        session_id: str,
        payload: dict,
    ) -> None:
        self._validate(session_id, payload)
        execution_session_id = str(
            payload.get("session_id", "")
        ).strip()

        await self.coordinator.execute(
            websocket,
            transport_session_id=session_id,
            execution_session_id=execution_session_id,
            payload=payload,
        )
        self.handle_count += 1

    def ready(self) -> bool:
        return (
            self.coordinator is not None
            and self.coordinator.ready()
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "handled": self.handle_count,
            "coordinator": self.coordinator.dump(),
        }

    @staticmethod
    def _validate(session_id: str, payload: Any) -> None:
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("transport session id required")
        if not isinstance(payload, dict):
            raise TypeError("payload must dict")


__all__ = ["WSAgentHandler"]
