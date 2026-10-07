"""gateway streaming 扩展（单一职责）。

设计：双路径，不破坏现有同步 gateway。
  · RAG_AGENT_STREAM=1  → 用 streaming
  · RAG_AGENT_STREAM=0  → 保持同步（默认）
"""
from backend.agent_tools.streaming.ollama_stream import (
    is_enabled, stream_ollama_chat,
)

__all__ = ["is_enabled", "stream_ollama_chat"]
