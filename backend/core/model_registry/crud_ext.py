"""Provider / Model CRUD 扩展（独立职责，不改 facade 核心）"""
from typing import Any, Dict, List

from .domain import ProviderConfig
from .persistence import save as _save
from .registry import get_registry

def update_provider(pid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    reg = get_registry()
    old = reg.providers.get(pid)
    if not old:
        raise KeyError("provider not found: " + pid)
    new = ProviderConfig(
        id=old.id,
        name=patch.get("name", old.name),
        kind=patch.get("kind", old.kind),
        base_url=patch.get("base_url", old.base_url),
        api_key=patch.get("api_key", old.api_key),
        enabled=patch.get("enabled", old.enabled),
    )
    reg.register_provider(new)
    reg.discover_models()
    _save(reg)
    return {"ok": True, "id": pid}

def delete_provider(pid: str) -> Dict[str, Any]:
    reg = get_registry()
    if pid not in reg.providers:
        raise KeyError("provider not found: " + pid)
    del reg.providers[pid]
    reg.plugins.pop(pid, None)
    for mid in [m.id for m in reg.models.values() if m.provider_id == pid]:
        reg.models.pop(mid, None)
    _save(reg)
    return {"ok": True, "id": pid}

def list_all_models() -> List[Dict[str, Any]]:
    reg = get_registry()
    return [
        {"id": m.id, "provider": m.provider_id,
         "display": m.display_name or m.id,
         "ctx": m.context_window, "cost_per_1k": m.cost_per_1k}
        for m in reg.models.values()
    ]

def usage_kpi() -> Dict[str, Any]:
    reg = get_registry()
    by_provider: Dict[str, int] = {}
    for m in reg.models.values():
        by_provider[m.provider_id] = by_provider.get(m.provider_id, 0) + 1
    total_cost = 0.0
    routed = 0
    for r in reg.roles.values():
        m = reg.models.get(r.primary)
        if m:
            routed += 1
            total_cost += m.cost_per_1k
    return {
        "models_by_provider": by_provider,
        "avg_role_cost_per_1k": round(total_cost / routed, 4) if routed else 0.0,
        "roles_routed": routed,
        "total_models": len(reg.models),
        "total_roles": len(reg.roles),
    }
