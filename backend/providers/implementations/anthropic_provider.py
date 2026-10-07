"""Anthropic Claude provider — Messages API。"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

import httpx

from backend.providers._shared.llm_base import LLMProviderBase
from backend.providers._shared.param_mapper import map_params

DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
ANTHROPIC_VERSION = "2023-06-01"


def _split_system(messages: List[Dict[str, Any]]) -> tuple:
    system_msgs = [m for m in messages if m.get("role") == "system"]
    user_msgs = [m for m in messages if m.get("role") != "system"]
    system_text = "\n".join(
        str(m.get("content", "")) for m in system_msgs
    )
    return system_text, user_msgs


class AnthropicProvider(LLMProviderBase):
    VERSION = "2.0"
    PROVIDER_TYPE = "anthropic"
    supports_tool_call = True
    supports_embedding = False

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        name: str = "anthropic",
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
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
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
        system_text, user_msgs = _split_system(messages)
        payload: Dict[str, Any] = {
            "model": model, "messages": user_msgs, **native,
        }
        if system_text:
            payload["system"] = system_text
        async with self._client() as c:
            r = await c.post("/v1/messages", json=payload)
        r.raise_for_status()
        blocks = r.json().get("content", [])
        return "".join(
            b.get("text", "") for b in blocks
            if b.get("type") == "text"
        )

    async def stream_chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> AsyncIterator[str]:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        system_text, user_msgs = _split_system(messages)
        payload: Dict[str, Any] = {
            "model": model, "messages": user_msgs,
            "stream": True, **native,
        }
        if system_text:
            payload["system"] = system_text
        async with self._client() as c:
            async with c.stream(
                "POST", "/v1/messages", json=payload,
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    yield line[len("data:"):].strip()

    async def embedding(
        self, texts: List[str], **kwargs: Any,
    ) -> List[List[float]]:
        raise NotImplementedError(
            "Anthropic does not expose embedding endpoint"
        )

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


__all__ = ["AnthropicProvider", "DEFAULT_BASE_URL", "DEFAULT_MODEL"]
