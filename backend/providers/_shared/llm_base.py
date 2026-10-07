"""LLM provider base: 统一 chat(messages, **kwargs) 接口。

调用方只用统一语义，provider 自己翻译成原生 API。
新增 provider 只覆写 chat / stream_chat / embedding。
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

from backend.core.module.base_provider import BaseProvider
from backend.providers._shared.chat_types import UnifiedParams


class LLMProviderBase(BaseProvider):
    """Common template for all LLM providers."""

    COMPONENT_TYPE = "llm_provider"
    CATEGORY = "provider"
    PROVIDER_TYPE: str = "openai_compatible"

    supports_tool_call: bool = False
    supports_stream: bool = True
    supports_embedding: bool = False

    def __init__(self, name: str = "llm_provider") -> None:
        super().__init__(name=name)

    # ─── 统一接口（子类实现） ────────────────────────────
    async def chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> str:
        raise NotImplementedError

    async def stream_chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> AsyncIterator[str]:
        raise NotImplementedError
        yield ""  # pragma: no cover

    async def embedding(
        self, texts: List[str], **kwargs: Any,
    ) -> List[List[float]]:
        raise NotImplementedError

    # ─── 统一参数解析（子类调用） ─────────────────────────
    def _parse_kwargs(
        self, kwargs: Dict[str, Any],
    ) -> UnifiedParams:
        return UnifiedParams.from_kwargs(kwargs)

    # ─── core BaseProvider 兼容接口 ─────────────────────
    def execute(self, request: Any) -> Any:
        """core BaseProvider 要求；同步包装，仅作占位。"""
        raise NotImplementedError(
            "use `await chat(messages, ...)` instead"
        )

    def provide(self, request: Any) -> Any:
        """core BaseProvider 要求；LLM 场景请用 chat()。"""
        raise NotImplementedError(
            "use `await chat(messages, ...)` instead"
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        base = super().dump()
        base.update({
            "provider_type": self.PROVIDER_TYPE,
            "supports_tool_call": self.supports_tool_call,
            "supports_stream": self.supports_stream,
            "supports_embedding": self.supports_embedding,
        })
        return base


__all__ = ["LLMProviderBase"]
