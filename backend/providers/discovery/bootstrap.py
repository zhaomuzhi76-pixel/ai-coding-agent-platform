"""启动时扫描所有 ollama provider，发现并缓存模型。"""
from __future__ import annotations

from typing import Any

from backend.providers.config import load_llm_config

from .merger import merge_into_config
from .ollama_discovery import discover_ollama_models

_CACHE: dict[str, list[dict[str, Any]]] = {}
_READY = False


async def refresh_ollama_discovery() -> dict[str, list[dict[str, Any]]]:
    """扫描 config 里所有 type=ollama 的 provider，发现模型。

    结果缓存在模块级 _CACHE，供 API 层合并。
    失败不抛异常（降级：走 yaml 里手写的 models）。
    """
    global _CACHE, _READY
    try:
        cfg = load_llm_config()
    except Exception as e:
        print(f"[discovery] load_llm_config failed: {e}", flush=True)
        return _CACHE

    new_cache: dict[str, list[dict[str, Any]]] = {}
    for p in cfg.providers:
        if p.type != "ollama":
            continue
        try:
            models = await discover_ollama_models(p.base_url)
            if models:
                new_cache[p.name] = models
                print(
                    f"[discovery] {p.name}: {len(models)} chat models",
                    flush=True,
                )
        except Exception as e:
            print(
                f"[discovery] {p.name} failed: "
                f"{type(e).__name__}: {e}",
                flush=True,
            )

    _CACHE = new_cache
    _READY = True
    return _CACHE


def get_discovered(provider_name: str) -> list[dict[str, Any]]:
    return list(_CACHE.get(provider_name, []))


def get_all_discovered() -> dict[str, list[dict[str, Any]]]:
    return {k: list(v) for k, v in _CACHE.items()}


def is_ready() -> bool:
    return _READY


__all__ = [
    "refresh_ollama_discovery",
    "get_discovered",
    "get_all_discovered",
    "is_ready",
    "merge_into_config",
]
