"""统一参数 → 各 provider 原生参数。

新增 provider 只加一个映射函数，调用方零改动。
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from backend.providers._shared.chat_types import UnifiedParams


def to_ollama(p: UnifiedParams) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if p.format == "json":
        out["format"] = "json"
    options: Dict[str, Any] = {"temperature": p.temperature}
    if p.max_tokens is not None:
        options["num_predict"] = p.max_tokens
    if p.top_p is not None:
        options["top_p"] = p.top_p
    if p.stop:
        options["stop"] = p.stop
    out["options"] = options
    if p.tools:
        out["tools"] = p.tools
    out.update(p.extra)
    return out


def to_openai(p: UnifiedParams) -> Dict[str, Any]:
    out: Dict[str, Any] = {"temperature": p.temperature}
    if p.format == "json":
        out["response_format"] = {"type": "json_object"}
    if p.max_tokens is not None:
        out["max_tokens"] = p.max_tokens
    if p.top_p is not None:
        out["top_p"] = p.top_p
    if p.stop:
        out["stop"] = p.stop
    if p.tools:
        out["tools"] = p.tools
    if p.thinking:
        out["extra_body"] = {"enable_thinking": True}
    out.update(p.extra)
    return out


def to_anthropic(p: UnifiedParams) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "temperature": p.temperature,
        "max_tokens": p.max_tokens if p.max_tokens else 4096,
    }
    if p.top_p is not None:
        out["top_p"] = p.top_p
    if p.stop:
        out["stop_sequences"] = p.stop
    if p.thinking:
        out["thinking"] = {"type": "enabled", "budget_tokens": 2048}
    if p.tools:
        out["tools"] = p.tools
    out.update(p.extra)
    return out


def to_gemini(p: UnifiedParams) -> Dict[str, Any]:
    out: Dict[str, Any] = {"temperature": p.temperature}
    if p.format == "json":
        out["response_mime_type"] = "application/json"
    if p.max_tokens is not None:
        out["max_output_tokens"] = p.max_tokens
    if p.top_p is not None:
        out["top_p"] = p.top_p
    if p.stop:
        out["stop_sequences"] = p.stop
    out.update(p.extra)
    return out


_MAPPERS: Dict[str, Callable[[UnifiedParams], Dict[str, Any]]] = {
    "ollama": to_ollama,
    "openai_compatible": to_openai,
    "openai": to_openai,
    "deepseek": to_openai,
    "dashscope": to_openai,
    "dashscope-maas": to_openai,
    "anthropic": to_anthropic,
    "claude": to_anthropic,
    "gemini": to_gemini,
}


def map_params(provider_type: str, params: UnifiedParams) -> Dict[str, Any]:
    fn = _MAPPERS.get(provider_type, to_openai)
    return fn(params)


def map_kwargs(provider_type: str, **kwargs: Any) -> Dict[str, Any]:
    return map_params(provider_type, UnifiedParams.from_kwargs(kwargs))


def registered_providers() -> list:
    return sorted(_MAPPERS.keys())


__all__ = [
    "to_ollama", "to_openai", "to_anthropic", "to_gemini",
    "map_params", "map_kwargs", "registered_providers",
]
