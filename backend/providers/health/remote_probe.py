"""远程 provider 真实连通性探测。

工业级契约：
  - 用 /models 端点探测（不消耗 token 额度）
  - 超时 5 秒
  - 401/403 → unhealthy
"""
from __future__ import annotations

import time
from typing import Any

import httpx

_TIMEOUT = 5.0


async def probe_remote(
    spec: dict[str, Any],
) -> tuple[bool, str, float]:
    ptype = (spec.get("type") or "").strip()
    base_url = (spec.get("base_url") or "").rstrip("/")
    api_key = (spec.get("api_key") or "").strip()

    if not base_url:
        return False, "base_url missing", 0.0
    if not api_key:
        return False, "api_key missing", 0.0

    if ptype == "anthropic":
        url = f"{base_url}/v1/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
    elif ptype in ("dashscope", "openai_compatible"):
        url = f"{base_url}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
    else:
        return False, f"unsupported type: {ptype}", 0.0

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.get(url, headers=headers)
            latency = (time.perf_counter() - start) * 1000
            if r.status_code == 200:
                return True, "", latency
            return False, f"HTTP {r.status_code}", latency
    except httpx.TimeoutException:
        latency = (time.perf_counter() - start) * 1000
        return False, "timeout", latency
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        return False, f"{type(exc).__name__}: {exc}", latency


__all__ = ["probe_remote"]
