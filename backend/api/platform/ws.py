"""Platform WS: 流式推送 propose 事件。

路径 /ws/platform
收到：{"action": "propose", "session_id", "task", "files", "workspace", "model"}
推送：
    {"event": "plan", ...}
    {"event": "token", "text": "..."}
    {"event": "stage", ...}
    {"event": "done", ...}
    {"event": "error", "reason": "..."}
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.platform import CodingRequest


router = APIRouter()


class PlatformWSHandler:
    VERSION = "1.0"

    def __init__(self, binding_factory: Any) -> None:
        if binding_factory is None:
            raise ValueError("binding_factory required")
        self._factory = binding_factory
        self._binding = None

    def _get_binding(self):
        if self._binding is None:
            self._binding = self._factory()
        return self._binding

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        binding = self._get_binding()

        try:
            while True:
                payload = await websocket.receive_json()
                if not isinstance(payload, dict):
                    await self._send(websocket, {
                        "event": "error",
                        "reason": "payload must dict",
                    })
                    continue
                try:
                    await self._dispatch(websocket, binding, payload)
                except Exception as exc:
                    await self._send(websocket, {
                        "event": "error",
                        "reason": f"{type(exc).__name__}: {exc}",
                    })
        except WebSocketDisconnect:
            return

    async def _dispatch(
        self, websocket: WebSocket, binding: Any, payload: dict,
    ) -> None:
        action = str(payload.get("action", "propose")).strip()
        if action != "propose":
            await self._send(websocket, {
                "event": "error",
                "reason": f"unknown action: {action}",
            })
            return

        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            await self._send(websocket, {
                "event": "error", "reason": "session_id required",
            })
            return

        async def emit(evt: dict) -> None:
            await self._send(websocket, evt)

        # 直接调 pipeline.propose，带 event_callback
        pipeline = binding.platform._pipeline
        session = binding.platform.get_session(session_id)

        req = CodingRequest(
            task=str(payload.get("task", "")),
            files=list(payload.get("files") or ["unknown.py"]),
            workspace=str(
                payload.get("workspace", session.workspace),
            ),
            model=str(payload.get("model", session.model)),
            locale=session.locale,
        )
        proposal = await pipeline.propose(
            session, req,
            gateway=binding._gateway,
            router=binding._router,
            event_callback=emit,
        )
        # 注册到 platform 的 proposals
        binding.platform._proposals[proposal.proposal_id] = proposal

    async def _send(self, websocket: WebSocket, evt: dict) -> None:
        try:
            await websocket.send_json(evt)
        except Exception as e:
            swallow("api.platform.ws:110", e, level="warn")

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


_BINDING_SINGLETON = None


def _build_binding():
    """WS 和 REST 共享同一个 PlatformBinding（同 sessions/proposals）。"""
    global _BINDING_SINGLETON
    if _BINDING_SINGLETON is not None:
        return _BINDING_SINGLETON
    from backend.api.platform.binding import PlatformBinding
    from backend.api.platform.factory import (
        _build_platform, _build_catalog, _build_domain_registry,
    )
    try:
        from backend.runtime.executors.runtime_dependencies import (
            get_runtime_deps,
        )
        deps = get_runtime_deps()
    except Exception:
        deps = {}
    _BINDING_SINGLETON = PlatformBinding(
        platform_factory=_build_platform,
        model_catalog=_build_catalog(),
        domain_registry=_build_domain_registry(),
        gateway=deps.get("gateway"),
        router=deps.get("router"),
    )
    return _BINDING_SINGLETON


_handler = PlatformWSHandler(binding_factory=_build_binding)


@router.websocket("/ws/platform")
async def ws_platform(websocket: WebSocket):
    await _handler.handle(websocket)


__all__ = ["router", "PlatformWSHandler"]
