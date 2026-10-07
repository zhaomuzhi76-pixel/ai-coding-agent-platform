"""IPC 消息协议（父进程 ↔ 子进程）。

契约：
  - 一行一个 JSON，UTF-8
  - 每条消息必须有 type
  - task/step/result/error 必须 session_id + task_id 非空
  - ready/shutdown/ping/pong 免 session_id
  - 命名具体化：encode_message / decode_message（避免与 mcp/jsonrpc 撞名）

不负责：
  - 网络传输 / 业务逻辑 / agent 执行 / 消息路由
"""
from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = "1.0"

MSG_READY = "ready"
MSG_SHUTDOWN = "shutdown"
MSG_PING = "ping"
MSG_PONG = "pong"
MSG_TASK = "task"
MSG_STEP = "step"
MSG_RESULT = "result"
MSG_ERROR = "error"

_ALL_TYPES = frozenset({
    MSG_READY, MSG_SHUTDOWN, MSG_PING, MSG_PONG,
    MSG_TASK, MSG_STEP, MSG_RESULT, MSG_ERROR,
})
_REQUIRES_SESSION = frozenset({MSG_TASK, MSG_STEP, MSG_RESULT, MSG_ERROR})


class ProtocolError(ValueError):
    """IPC 协议违规。"""


def _session(session_id: Any) -> str:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ProtocolError("session_id required")
    return session_id


def _task_id(task_id: Any) -> str:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ProtocolError("task_id required")
    return task_id


def make_ready(worker_id: str) -> dict[str, Any]:
    return {"type": MSG_READY, "version": PROTOCOL_VERSION,
            "worker_id": str(worker_id)}


def make_shutdown() -> dict[str, Any]:
    return {"type": MSG_SHUTDOWN, "version": PROTOCOL_VERSION}


def make_ping() -> dict[str, Any]:
    return {"type": MSG_PING, "version": PROTOCOL_VERSION}


def make_pong() -> dict[str, Any]:
    return {"type": MSG_PONG, "version": PROTOCOL_VERSION}


def make_task(*, session_id: str, task_id: str, message: str,
              workspace: str, provider: str, model: str,
              base_url: str = "", api_key: str = "",
              max_steps: int = 10) -> dict[str, Any]:
    return {
        "type": MSG_TASK, "version": PROTOCOL_VERSION,
        "session_id": _session(session_id),
        "task_id": _task_id(task_id),
        "message": str(message), "workspace": str(workspace),
        "provider": str(provider), "model": str(model),
        "base_url": str(base_url), "api_key": str(api_key),
        "max_steps": int(max_steps),
    }


def make_step(*, session_id: str, task_id: str,
              entry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ProtocolError("step entry must be dict")
    return {
        "type": MSG_STEP, "version": PROTOCOL_VERSION,
        "session_id": _session(session_id),
        "task_id": _task_id(task_id),
        "entry": entry,
    }


def make_result(*, session_id: str, task_id: str,
                result: Any) -> dict[str, Any]:
    return {
        "type": MSG_RESULT, "version": PROTOCOL_VERSION,
        "session_id": _session(session_id),
        "task_id": _task_id(task_id),
        "result": result,
    }


def make_error(*, session_id: str, task_id: str,
               error: str) -> dict[str, Any]:
    if not isinstance(error, str) or not error.strip():
        raise ProtocolError("error message required")
    return {
        "type": MSG_ERROR, "version": PROTOCOL_VERSION,
        "session_id": _session(session_id),
        "task_id": _task_id(task_id),
        "error": error,
    }


def validate(msg: Any) -> dict[str, Any]:
    if not isinstance(msg, dict):
        raise ProtocolError("message must be dict")
    mtype = msg.get("type")
    if mtype not in _ALL_TYPES:
        raise ProtocolError("unknown type: " + repr(mtype))
    if mtype in _REQUIRES_SESSION:
        _session(msg.get("session_id"))
        _task_id(msg.get("task_id"))
    return msg


def encode_message(msg: dict[str, Any]) -> bytes:
    validate(msg)
    text = json.dumps(msg, ensure_ascii=False, separators=(",", ":"))
    return (text + chr(10)).encode("utf-8")


def decode_message(line: Any) -> Any:
    if isinstance(line, (bytes, bytearray)):
        try:
            line = bytes(line).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProtocolError("invalid utf-8") from exc
    if not isinstance(line, str):
        raise ProtocolError("line must be bytes or str")
    text = line.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise ProtocolError("invalid json") from exc
    return validate(obj)


__all__ = [
    "PROTOCOL_VERSION", "ProtocolError",
    "MSG_READY", "MSG_SHUTDOWN", "MSG_PING", "MSG_PONG",
    "MSG_TASK", "MSG_STEP", "MSG_RESULT", "MSG_ERROR",
    "make_ready", "make_shutdown", "make_ping", "make_pong",
    "make_task", "make_step", "make_result", "make_error",
    "validate", "encode_message", "decode_message",
]
