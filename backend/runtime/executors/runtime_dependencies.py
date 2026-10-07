from __future__ import annotations

from typing import Any

_DEPS: dict[str, Any] = {
    "gateway": None,
    "router": None,
    "orchestrator": None,
}


def set_runtime_deps(
    *,
    gateway: Any = None,
    router: Any = None,
    orchestrator: Any = None,
) -> None:
    """应用层装配完成后调用，把依赖注册到全局。"""
    if gateway is not None:
        _DEPS["gateway"] = gateway
    if router is not None:
        _DEPS["router"] = router
    if orchestrator is not None:
        _DEPS["orchestrator"] = orchestrator
    print(
        f"[runtime-deps] SET gateway={type(_DEPS['gateway']).__name__} "
        f"router={type(_DEPS['router']).__name__} "
        f"orchestrator={type(_DEPS['orchestrator']).__name__}",
        flush=True,
    )


def get_runtime_deps() -> dict[str, Any]:
    deps = dict(_DEPS)
    print(
        f"[runtime-deps] GET gateway={'YES' if deps['gateway'] else 'NO'} "
        f"router={'YES' if deps['router'] else 'NO'} "
        f"orchestrator={'YES' if deps['orchestrator'] else 'NO'}",
        flush=True,
    )
    return deps


def clear_runtime_deps() -> None:
    _DEPS["gateway"] = None
    _DEPS["router"] = None
    _DEPS["orchestrator"] = None
    print("[runtime-deps] CLEARED", flush=True)


__all__ = ["set_runtime_deps", "get_runtime_deps", "clear_runtime_deps"]
