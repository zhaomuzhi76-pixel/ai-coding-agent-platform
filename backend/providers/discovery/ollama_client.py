"""Ollama /api/tags HTTP 客户端。"""
from __future__ import annotations

from typing import Any

import httpx

_TIMEOUT = 5.0


async def fetch_ollama_models(
    base_url: str,
) -> list[dict[str, Any]]:
    """调 /api/tags 返回原始模型列表。失败返回空列表。"""
    if not base_url:
        return []
    url = base_url.rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.get(url)
            r.raise_for_status()
            data = r.json()
            return list(data.get("models", []) or [])
    except Exception:
        return []


__all__ = ["fetch_ollama_models"]
