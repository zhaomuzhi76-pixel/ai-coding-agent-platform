"""ProviderTester: 单次轻量探活，验证 provider 是否可用。"""
from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, Optional


_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _resolve_key(raw: str) -> str:
    """解析 key，清理所有空白 / 换行 / 不可见字符。

    HTTP header 不允许换行，用户从控制台复制经常带 '\n'。
    """
    if not raw:
        return ""
    def repl(m):
        return os.environ.get(m.group(1), "")
    resolved = _ENV_RE.sub(repl, raw)
    # 去掉所有空白字符（含 \n \r \t 空格），header 不允许
    return "".join(resolved.split())


async def test_provider(payload: Dict[str, Any]) -> Dict[str, Any]:
    ptype = str(payload.get("type", "")).strip()
    base_url = str(payload.get("base_url", "")).strip().rstrip("/")
    api_key = _resolve_key(str(payload.get("api_key", "")))
    model = ""
    models = payload.get("models") or []
    if models and isinstance(models[0], dict):
        model = str(models[0].get("id", "")).strip()
    if not base_url:
        return {"success": False, "error": "base_url required"}

    t0 = time.perf_counter()
    try:
        if ptype == "ollama":
            return await _test_ollama(base_url, model, t0)
        if ptype in ("openai_compatible", "dashscope",
                     "deepseek", "gemini"):
            return await _test_openai(base_url, api_key, model, t0)
        if ptype == "anthropic":
            return await _test_anthropic(base_url, api_key, model, t0)
        return {"success": False, "error": f"unsupported type: {ptype}"}
    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": (time.perf_counter() - t0) * 1000,
        }


async def _test_ollama(base_url, model, t0) -> Dict[str, Any]:
    import httpx
    async with httpx.AsyncClient(timeout=5.0) as c:
        r = await c.get(f"{base_url}/api/tags")
        r.raise_for_status()
        tags = r.json().get("models", [])
    names = [m.get("name", "") for m in tags]
    if model and not any(m == model or m.startswith(model.split(":")[0])
                         for m in names):
        return {
            "success": False,
            "error": f"model not found: {model}",
            "available_models": names[:20],
            "latency_ms": (time.perf_counter() - t0) * 1000,
        }
    return {
        "success": True,
        "models_count": len(names),
        "latency_ms": (time.perf_counter() - t0) * 1000,
    }


async def _test_openai(base_url, api_key, model, t0) -> Dict[str, Any]:
    import httpx
    if not api_key:
        return {"success": False, "error": "api_key required"}
    if not model:
        return {"success": False, "error": "model required"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 3,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=20.0) as c:
        r = await c.post(
            f"{base_url}/chat/completions",
            headers=headers, json=payload,
        )
    latency = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    # 解析错误
    try:
        err = r.json()
        msg = err.get("error", {}).get("message", str(err))
    except Exception:
        msg = r.text[:200]
    return {
        "success": False,
        "error": f"HTTP {r.status_code}: {msg[:200]}",
        "latency_ms": latency,
    }


async def _test_anthropic(base_url, api_key, model, t0) -> Dict[str, Any]:
    import httpx
    if not api_key:
        return {"success": False, "error": "api_key required"}
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "claude-3-5-sonnet-20241022",
        "max_tokens": 3,
        "messages": [{"role": "user", "content": "hi"}],
    }
    async with httpx.AsyncClient(timeout=20.0) as c:
        r = await c.post(
            f"{base_url}/v1/messages", headers=headers, json=payload,
        )
    latency = (time.perf_counter() - t0) * 1000
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    try:
        msg = r.json().get("error", {}).get("message", r.text[:200])
    except Exception:
        msg = r.text[:200]
    return {"success": False, "error": f"HTTP {r.status_code}: {msg[:200]}",
            "latency_ms": latency}


__all__ = ["test_provider"]
