"""Ollama LLM / embedding provider."""
from __future__ import annotations
from backend.core.model_registry.embedding_resolver import resolve_embedding_model
from backend.config.constants.endpoints import (
    OLLAMA_URL,
)

import json
from typing import Any, AsyncIterator, Dict, List

import httpx

from backend.providers._shared.llm_base import LLMProviderBase
from backend.providers._shared.param_mapper import map_params

# 默认 keep_alive：延长模型驻留时间（5min → 30min）
DEFAULT_KEEP_ALIVE = "30m"

# 模块级共享 httpx 客户端（连接池复用）
_shared_client: httpx.AsyncClient | None = None


def _get_shared_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=30.0,
            ),
        )
    return _shared_client


async def close_shared_client() -> None:
    global _shared_client
    if _shared_client is not None:
        try:
            await _shared_client.aclose()
        except Exception:  # silent-ok
            pass
        _shared_client = None


class OllamaProvider(LLMProviderBase):
    """Ollama provider（统一语义 → 原生 Ollama 参数）。"""

    VERSION = "7.1"
    PROVIDER_TYPE = "ollama"

    def __init__(
        self,
        model: str,
        base_url: str = OLLAMA_URL,
        embedding_model: str = "",
        name: str = "ollama",
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model required")
        super().__init__(name=name)
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.embedding_model = embedding_model.strip()

    async def chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> str:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        keep_alive = native.pop("keep_alive", DEFAULT_KEEP_ALIVE)
        payload = {
            "model": model, "messages": messages,
            "stream": False,
            "keep_alive": keep_alive,
            **native,
        }
        client = _get_shared_client()
        r = await client.post(f"{self.base_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")

    async def stream_chat(
        self, messages: List[Dict[str, Any]], **kwargs: Any,
    ) -> AsyncIterator[str]:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.model
        native = map_params(self.PROVIDER_TYPE, params)
        keep_alive = native.pop("keep_alive", DEFAULT_KEEP_ALIVE)
        payload = {
            "model": model, "messages": messages,
            "stream": True,
            "keep_alive": keep_alive,
            **native,
        }
        client = _get_shared_client()
        async with client.stream(
            "POST", f"{self.base_url}/api/chat", json=payload,
        ) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                text = data.get("message", {}).get("content", "")
                if text:
                    yield text
                if data.get("done"):
                    break

    async def embedding(
        self, texts: List[str], **kwargs: Any,
    ) -> List[List[float]]:
        params = self._parse_kwargs(kwargs)
        model = params.model or self.embedding_model
        client = _get_shared_client()
        r = await client.post(
            f"{self.base_url}/api/embed",
            json={"model": model, "input": texts,
                  "keep_alive": DEFAULT_KEEP_ALIVE},
        )
        r.raise_for_status()
        return r.json().get("embeddings", [])

    def ready(self) -> bool:
        return bool(self.base_url and self.model)

    def dump(self) -> Dict[str, Any]:
        base = super().dump()
        base.update({
            "model": self.model,
            "embedding_model": self.embedding_model,
            "base_url": self.base_url,
            "keep_alive": DEFAULT_KEEP_ALIVE,
        })
        return base


__all__ = ["OllamaProvider", "close_shared_client", "DEFAULT_KEEP_ALIVE"]
