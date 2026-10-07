"""从配置解析 provider 实例 + 构造 runner 依赖（L3）。

职责：
    - 读 load_llm_config() 拿 provider 配置
    - 按 type 构造 provider 实例（Ollama / OpenAICompatible / ...）
    - 提供 chat_fn / stream_fn / cost_fn 供 BenchmarkRunner 注入

不负责：
    - 跑测（runner 管）
    - 持久化（store 管）
    - HTTP（api 管）

设计：
    不依赖 ProviderAssemblyBuilder（那套给 runtime 用），
    直接构造轻量 provider 实例——benchmark 只需 chat/stream 能力。

命名具体化：
    resolve_provider_instance / build_chat_fn / build_runner_for
"""
from __future__ import annotations

from typing import Any

from backend.providers.config import load_llm_config
from backend.providers.implementations.ollama_provider import OllamaProvider
from backend.providers.implementations.openai_provider import OpenAICompatibleProvider
from backend.providers.implementations.dashscope_provider import DashScopeProvider
from backend.providers.implementations.anthropic_provider import AnthropicProvider

from .runner import BenchmarkRunner


_TYPE_CLASS = {
    "ollama": OllamaProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "dashscope": DashScopeProvider,
    "anthropic": AnthropicProvider,
}

_NEEDS_API_KEY = {"openai_compatible", "dashscope", "anthropic"}


def resolve_provider_instance(provider_name: str, model_id: str) -> Any:
    """按 provider 名 + model 名构造 provider 实例。

    抛出：
        ValueError — provider 不存在 / 类型不支持 / 缺 api_key
    """
    if not isinstance(provider_name, str) or not provider_name.strip():
        raise ValueError("provider_name required")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("model_id required")

    cfg = load_llm_config()
    p = None
    for candidate in cfg.providers:
        if getattr(candidate, "name", "") == provider_name.strip():
            p = candidate
            break
    if p is None:
        raise ValueError(f"provider not found: {provider_name}")

    ptype = str(getattr(p, "type", "")).strip()
    cls = _TYPE_CLASS.get(ptype)
    if cls is None:
        raise ValueError(f"unsupported provider type: {ptype}")

    base_url = str(getattr(p, "base_url", "") or "").strip()
    api_key = str(getattr(p, "api_key", "") or "").strip()

    kwargs: dict[str, Any] = {
        "model": model_id.strip(),
        "name": provider_name.strip(),
    }
    if base_url:
        kwargs["base_url"] = base_url
    if ptype in _NEEDS_API_KEY:
        if not api_key:
            raise ValueError(f"provider {provider_name} missing api_key")
        kwargs["api_key"] = api_key

    return cls(**kwargs)


def build_chat_fn(provider_name: str, model_id: str):
    """返回 chat_fn: (messages, kwargs) -> str。"""
    inst = resolve_provider_instance(provider_name, model_id)

    async def _chat(messages: list[dict], kwargs: dict) -> str:
        return await inst.chat(messages, **kwargs)

    return _chat


def build_stream_fn(provider_name: str, model_id: str):
    """返回 stream_fn: (messages, kwargs) -> AsyncIterator[str]。"""
    inst = resolve_provider_instance(provider_name, model_id)

    async def _stream(messages: list[dict], kwargs: dict):
        async for chunk in inst.stream_chat(messages, **kwargs):
            yield chunk

    return _stream


def build_cost_fn(provider_name: str, model_id: str):
    """返回 cost_fn: (provider, in_tok, out_tok) -> float。"""
    try:
        from backend.providers.cost.registry import get_tracker
        tracker = get_tracker()
    except Exception:
        return lambda p, i, o: 0.0

    def _cost(_provider: str, in_tok: int, out_tok: int) -> float:
        try:
            return float(tracker.calculate_cost(model_id, in_tok, out_tok))
        except Exception:
            return 0.0

    return _cost


def build_runner_for(
    provider_name: str,
    model_id: str,
    *,
    case_timeout_sec: float = 60.0,
    total_timeout_sec: float = 600.0,
) -> BenchmarkRunner:
    """一站式：构造完整的 BenchmarkRunner。"""
    return BenchmarkRunner(
        chat_fn=build_chat_fn(provider_name, model_id),
        stream_fn=build_stream_fn(provider_name, model_id),
        cost_fn=build_cost_fn(provider_name, model_id),
        case_timeout_sec=case_timeout_sec,
        total_timeout_sec=total_timeout_sec,
    )


__all__ = [
    "resolve_provider_instance",
    "build_chat_fn",
    "build_stream_fn",
    "build_cost_fn",
    "build_runner_for",
]
