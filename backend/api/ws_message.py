from __future__ import annotations

from typing import Any


def _session(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session id required")


def build_step_message(
    session_id: str,
    event: dict[str, Any],
) -> dict[str, Any]:
    _session(session_id)

    if not isinstance(event, dict):
        raise TypeError("step event must dict")

    return {
        "type": "step",
        "session_id": session_id,
        "data": event,
    }


def build_result_message(
    session_id: str,
    model: str,
    result: Any,
) -> dict[str, Any]:
    _session(session_id)

    # 工业级：错误帧/空 model 场景不阻塞送达；用 "unknown" 兜底
    if not isinstance(model, str) or not model.strip():
        model = "unknown"

    return {
        "type": "result",
        "session_id": session_id,
        "model": model,
        "data": result,
    }


def build_end_message(
    session_id: str,
    model: str,
) -> dict[str, Any]:
    _session(session_id)

    if not isinstance(model, str) or not model.strip():
        model = "unknown"

    return {
        "type": "end",
        "session_id": session_id,
        "model": model,
    }


def build_error_message(
    session_id: str,
    message: str,
) -> dict[str, Any]:
    _session(session_id)

    if not isinstance(message, str) or not message.strip():
        raise ValueError("error message required")

    return {
        "type": "error",
        "session_id": session_id,
        "data": message,
    }


__all__ = [
    "build_end_message",
    "build_error_message",
    "build_result_message",
    "build_step_message",
]
