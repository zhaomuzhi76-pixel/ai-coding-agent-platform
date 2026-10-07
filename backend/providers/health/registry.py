"""Health registry: 全局单例。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Optional

from backend.providers.health.checker import ProviderHealthChecker

_CHECKER: Optional[ProviderHealthChecker] = None


def _build_default() -> ProviderHealthChecker:
    checker = ProviderHealthChecker()
    try:
        from backend.providers.config import load_llm_config
        cfg = load_llm_config()
        for p in cfg.providers:
            checker.register(
                name=p.name, ptype=p.type,
                base_url=p.base_url, api_key=p.api_key,
            )
    except Exception as e:
        swallow("providers.health.registry:23", e)
    return checker


def get_checker() -> ProviderHealthChecker:
    global _CHECKER
    if _CHECKER is None:
        _CHECKER = _build_default()
    return _CHECKER


def reset() -> None:
    global _CHECKER
    _CHECKER = None


__all__ = ["get_checker", "reset"]
