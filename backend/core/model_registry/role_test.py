"""角色级测试 —— 走真实 gateway（通过 runtime_deps 拿）"""
import time
from typing import Any, Dict, List

from .registry import get_registry


def _candidates(reg, route) -> List[Dict[str, str]]:
    out = []
    for slot, mid in (("primary", route.primary),
                      ("fallback", route.fallback)):
        if not mid:
            continue
        m = reg.models.get(mid)
        if not m:
            out.append({"slot": slot, "model": mid,
                        "error": "未在 registry 注册"})
            continue
        out.append({"slot": slot, "model": mid, "provider": m.provider_id})
    return out


def _get_gateway():
    """从 runtime_deps 拿 gateway"""
    from backend.runtime.executors.runtime_dependencies import get_runtime_deps
    deps = get_runtime_deps()
    if not deps:
        raise RuntimeError("runtime_deps 未初始化")
    gw = deps.get("gateway")
    if gw is None:
        raise RuntimeError(f"deps 里无 gateway，现有键: {list(deps.keys())}")
    return gw


async def _real_call(provider: str, model: str):
    gw = _get_gateway()
    resp = await gw.chat(
        provider=provider,
        model=model,
        messages=[{"role": "user", "content": "ping"}],
        _role="role_test",
    )
    return resp


async def test_role(role: str) -> Dict[str, Any]:
    reg = get_registry()
    route = reg.roles.get(role)
    if not route:
        return {"ok": False, "error": f"role 未配置: {role}"}

    results = []
    for c in _candidates(reg, route):
        if "error" in c:
            results.append({**c, "ok": False})
            continue
        t0 = time.time()
        try:
            resp = await _real_call(c["provider"], c["model"])
            ms = int((time.time() - t0) * 1000)
            results.append({
                "slot": c["slot"], "model": c["model"],
                "provider": c["provider"], "ok": True,
                "latency_ms": ms, "sample": str(resp)[:80],
                "real_call": True,
            })
        except Exception as e:
            ms = int((time.time() - t0) * 1000)
            results.append({
                "slot": c["slot"], "model": c["model"],
                "provider": c["provider"], "ok": False,
                "latency_ms": ms,
                "error": f"{type(e).__name__}: {str(e)[:150]}",
            })

    return {
        "ok": all(r.get("ok") for r in results) and bool(results),
        "role": role, "results": results,
    }
