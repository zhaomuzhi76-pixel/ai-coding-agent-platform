from __future__ import annotations
from backend.core.observability.silent import swallow

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.api.ws_inbound_message_decoder import (
    WSInboundMessageDecoder,
    WSInboundProtocolError,
)
from backend.api.ws_protocol_error_delivery import (
    WSProtocolErrorDelivery,
)
from backend.api.ws_exception_policy import WSExceptionPolicy
from backend.api.ws_resilient_runner import WSResilientRunner


router = APIRouter()

HANDLER_STATE_KEY = "ws_agent_handler"
CONNECTION_MANAGER_STATE_KEY = "ws_agent_connection_manager"


def register_handler(
    handler,
    connection_manager,
    app_state=None,
) -> None:
    """
    Register transport dependencies into application state.

    Module-level mutable transport globals are intentionally avoided.
    """
    if handler is None:
        raise ValueError(
            "WSAgentHandler required"
        )

    if connection_manager is None:
        raise ValueError(
            "connection manager required"
        )

    if not handler.ready():
        raise RuntimeError(
            "WSAgentHandler not ready"
        )

    if app_state is None:
        raise ValueError(
            "application state required"
        )

    setattr(
        app_state,
        HANDLER_STATE_KEY,
        handler,
    )
    setattr(
        app_state,
        CONNECTION_MANAGER_STATE_KEY,
        connection_manager,
    )


def _handler(websocket: WebSocket):
    handler = getattr(
        websocket.app.state,
        HANDLER_STATE_KEY,
        None,
    )

    if handler is None:
        raise RuntimeError(
            "WSAgentHandler not initialized"
        )

    return handler


def _connection_manager(
    websocket: WebSocket,
):
    manager = getattr(
        websocket.app.state,
        CONNECTION_MANAGER_STATE_KEY,
        None,
    )

    if manager is None:
        raise RuntimeError(
            "connection manager not initialized"
        )

    return manager




async def _safe_error_send(
    error_delivery, websocket, session_id, msg,
) -> None:
    """工业级兜底：WS 已断开时不抛异常。"""
    try:
        from starlette.websockets import WebSocketState
        state = getattr(websocket, "client_state", None)
        if state is not None and state != WebSocketState.CONNECTED:
            return
    except Exception as e:
        swallow("api.ws_agent:110", e, level="warn")
    try:
        await error_delivery.send(websocket, session_id, msg)
    except Exception as e:
        swallow("api.ws_agent:114", e, level="warn")

@router.websocket("/ws/agent")
async def ws_agent(
    websocket: WebSocket,
):
    handler = _handler(websocket)
    manager = _connection_manager(websocket)
    decoder = WSInboundMessageDecoder()
    error_delivery = WSProtocolErrorDelivery()

    session_id = await manager.connect(
        websocket
    )

    # L2 装配：WSResilientRunner（心跳 + 异常分层）
    class _WSPolicy(WSExceptionPolicy):
        FATAL = WSExceptionPolicy.FATAL + (WebSocketDisconnect,)

    runner = WSResilientRunner(
        heartbeat_interval_sec=0,  # 协议层心跳由 uvicorn ws_ping_interval 负责
        policy=_WSPolicy(),
    )

    async def _receive() -> dict:
        try:
            return await decoder.decode(websocket)
        except WSInboundProtocolError as exc:
            # 连接已断 → 转致命，runner 退出（否则空帧无限循环）
            try:
                from starlette.websockets import (
                    WebSocketDisconnect, WebSocketState,
                )
                state = getattr(websocket, "client_state", None)
                if state is not None and state != WebSocketState.CONNECTED:
                    # WS 已断 → 干净退出循环，不传播异常
                    print(
                        "[ws_agent] WS disconnected (client_state), "
                        "graceful exit",
                        flush=True,
                    )
                    raise WebSocketDisconnect()
            except ImportError:
                pass
            # 其它协议错误 → 抛给 runner（会被 recoverable policy 处理）
            raise WSInboundProtocolError(str(exc)) from exc

    async def _handle(payload: dict) -> None:
        await handler.handle(websocket, session_id, payload)

    async def _send_error(msg: str) -> None:
        await _safe_error_send(
            error_delivery, websocket, session_id, msg,
        )

    try:
        await runner.run(
            receive=_receive,
            handle=_handle,
            send_error=_send_error,
            websocket=websocket,
        )
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as _exc:
        # graceful WS shutdown：单个 WS 断开不应拖垮整个进程
        print(
            f"[ws_agent] graceful WS shutdown: {type(_exc).__name__}: {_exc}",
            flush=True,
        )
        manager.disconnect(session_id)

__all__ = [
    "router",
    "register_handler",
]
