"""兼容层 - 现有代码字符串硬编码迁移到此（只做转发，不重复职责）"""
from .bootstrap import bootstrap_default
from .registry import get_registry

_booted = False


def _ensure() -> None:
    global _booted
    if not _booted:
        bootstrap_default()
        _booted = True


def _default_provider_id() -> str:
    _ensure()
    for pid in get_registry().providers:
        return pid
    return ""


def _default_role_model(role: str) -> str:
    _ensure()
    route = get_registry().get_role_route(role)
    return route.primary if route else ""


def _role_provider(role: str) -> str:
    _ensure()
    return get_registry().resolve_provider(role)
