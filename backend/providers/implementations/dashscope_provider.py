"""DashScope (阿里云百炼) provider — OpenAI 兼容端点。"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

import httpx

from backend.providers._shared.llm_base import LLMProviderBase
from backend.providers._shared.param_mapper import map_params

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-max"
DEFAULT_EMBEDDING_MODEL = "text-embedding-v3"


class DashScopeProvider(LLMProviderBase):
    VERSION = "2.0"
    PROVIDER_TYPE = "dashscope"
    supports_tool_call = True
    supports_embedding = True

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        name: str = "dashscope",
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key required")
        super().__init__(name=name)
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = default_model.strip()

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    async def chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> str:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        async with self._client() as c:
            r = await c.post(
                "/chat/completions",
                json={"model": model, "messages": messages, **native},
            )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    async def stream_chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> AsyncIterator[str]:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        async with self._client() as c:
            async with c.stream(
                "POST", "/chat/completions",
                json={
                    "model": model, "messages": messages,
                    "stream": True, **native,
                },
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[len("data:"):].strip()
                    if payload == "[DONE]":
                        break
                    yield payload

    async def embedding(
        self, texts: List[str], **kwargs: Any,
    ) -> List[List[float]]:
        params = self._parse_kwargs(kwargs)
        model = params.model or DEFAULT_EMBEDDING_MODEL
        async with self._client() as c:
            r = await c.post(
                "/embeddings",
                json={"model": model, "input": texts},
            )
        r.raise_for_status()
        return [item["embedding"] for item in r.json()["data"]]

    def ready(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def dump(self) -> Dict[str, Any]:
        base = super().dump()
        base.update({
            "base_url": self.base_url,
            "model": self.model,
            "has_api_key": bool(self.api_key),
        })
        return base


__all__ = ["DashScopeProvider", "DEFAULT_BASE_URL", "DEFAULT_MODEL"]
