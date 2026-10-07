"""gateway streaming 适配器（在同步 gateway 上叠加 token 回调）。

调用方：
    from backend.agent_tools.streaming.gateway_adapter import chat_with_stream
    text = await chat_with_stream(gateway, provider, messages, model, on_token)

行为：
  · RAG_AGENT_STREAM=1  → 走 streaming（token 回调）
  · RAG_AGENT_STREAM=0  → 走同步（原路径，0 影响）
"""
from __future__ import annotations
from typing import Any, Callable, Optional

from backend.agent_tools.streaming import ollama_stream


async def chat_with_stream(
    gateway: Any,
    provider: str,
    messages: list,
    model: str,
    *,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    """双路径 chat。streaming 失败自动回退同步。"""
    # 优先 streaming（仅 ollama + 启用）
    if ollama_stream.is_enabled() and provider in ("ollama", "ollama-local"):
        try:
            text = await ollama_stream.stream_ollama_chat(
                model, messages, on_token=on_token,
            )
            if text:
                return text
        except Exception:
            pass  # 回退

    # 同步原路径
    if hasattr(gateway, "chat"):
        return await gateway.chat(provider, messages, model)
    raise RuntimeError("gateway.chat not available")


def snapshot() -> dict:
    return {
        "stream_enabled": ollama_stream.is_enabled(),
        "ollama": ollama_stream.snapshot(),
    }


__all__ = ["chat_with_stream", "snapshot"]
