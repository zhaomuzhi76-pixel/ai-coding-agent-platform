"""OpenAI 兼容 provider（DeepSeek / DashScope MaaS / 自建网关都走这里）。"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

from backend.providers._shared.llm_base import LLMProviderBase
from backend.providers._shared.param_mapper import map_params


class OpenAICompatibleProvider(LLMProviderBase):
    """OpenAI 兼容端点（统一语义 → response_format / extra_body）。"""

    VERSION = "4.0"
    PROVIDER_TYPE = "openai_compatible"
    supports_tool_call = True

    def __init__(
        self,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        name: str = "openai_compatible",
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model required")
        if not api_key or not api_key.strip():
            raise ValueError("api_key required")
        super().__init__(name=name)
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.api_key = api_key.strip()

    def _client(self):
        try:
            from openai import AsyncOpenAI  # noqa: WPS433
        except ImportError as exc:
            raise RuntimeError(
                "openai sdk required: pip install openai"
            ) from exc
        return AsyncOpenAI(
            api_key=self.api_key, base_url=self.base_url, timeout=30,
        )

    async def chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> str:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        client = self._client()
        r = await client.chat.completions.create(
            model=model, messages=messages, **native,
        )
        return r.choices[0].message.content or ""

    async def stream_chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> AsyncIterator[str]:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        native["stream"] = True
        client = self._client()
        stream = await client.chat.completions.create(
            model=model, messages=messages, **native,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def embedding(
        self, texts: List[str], **kwargs: Any,
    ) -> List[List[float]]:
        params = self._parse_kwargs(kwargs)
        model = params.model or "text-embedding-3-small"
        client = self._client()
        r = await client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in r.data]

    def ready(self) -> bool:
        return bool(self.base_url and self.model and self.api_key)

    def dump(self) -> Dict[str, Any]:
        base = super().dump()
        base.update({
            "model": self.model,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
        })
        return base


OpenAIProvider = OpenAICompatibleProvider

__all__ = ["OpenAICompatibleProvider", "OpenAIProvider"]
