"""Ollama 流式客户端（单一职责：调 /api/chat stream=True 并逐块 yield）。

env:
  RAG_AGENT_STREAM           0/1（默认 0）
  OLLAMA_HOST                默认 http://127.0.0.1:11434
  RAG_AGENT_STREAM_TIMEOUT   默认 60（秒）

不做：解析 tool_call、循环控制、状态管理（各归其位）。
"""
from __future__ import annotations
import asyncio
import json
import os
import urllib.request
from typing import AsyncIterator, Optional


def is_enabled() -> bool:
    v = os.environ.get("RAG_AGENT_STREAM", "0").strip().lower()
    return v in ("1", "true", "yes", "on")


def _host() -> str:
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def _timeout() -> float:
    try:
        return float(os.environ.get("RAG_AGENT_STREAM_TIMEOUT", "60"))
    except ValueError:
        return 60.0


async def stream_ollama_chat(
    model: str,
    messages: list,
    *,
    on_token=None,
) -> str:
    """同步调用 ollama /api/chat（stream=true），逐块调 on_token，返回完整文本。

    注意：ollama stream 是同步 HTTP（urllib），用 to_thread 包在 asyncio 里。
    """
    if not is_enabled():
        # 未启用 → 返回空，让调用方走原路径
        return ""

    def _sync_call() -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{_host()}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        buf = []
        with urllib.request.urlopen(req, timeout=_timeout()) as r:
            for raw_line in r:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message") or {}
                chunk = msg.get("content", "")
                if chunk:
                    buf.append(chunk)
                    if on_token:
                        try:
                            on_token(chunk)
                        except Exception:
                            pass
                if obj.get("done") is True:
                    break
        return "".join(buf)

    return await asyncio.to_thread(_sync_call)


def snapshot() -> dict:
    return {
        "enabled": is_enabled(),
        "host": _host(),
        "timeout": _timeout(),
    }


__all__ = ["is_enabled", "stream_ollama_chat", "snapshot"]
