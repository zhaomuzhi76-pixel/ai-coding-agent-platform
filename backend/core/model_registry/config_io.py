"""配置导入导出（JSON + 手写 YAML，不依赖 PyYAML）"""
import json
from typing import Any, Dict

def _to_payload(reg) -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "providers": [
            {"id": p.id, "name": p.name, "kind": p.kind,
             "base_url": p.base_url, "api_key": p.api_key,
             "enabled": p.enabled}
            for p in reg.providers.values()
        ],
        "roles": [
            {"role": r.role, "primary": r.primary,
             "fallback": r.fallback, "params": r.params}
            for r in reg.roles.values()
        ],
    }

def export_json(reg) -> str:
    return json.dumps(_to_payload(reg), ensure_ascii=False, indent=2)

def _yaml_quote(v: str) -> str:
    s = str(v or "")
    if any(c in s for c in ":#\"'\n"):
        return '"' + s.replace('"', '\\"') + '"'
    return s

def export_yaml(reg) -> str:
    p = _to_payload(reg)
    out = ["version: " + p["version"], "providers:"]
    for x in p["providers"]:
        out.append("  - id: " + _yaml_quote(x["id"]))
        out.append("    name: " + _yaml_quote(x["name"]))
        out.append("    kind: " + _yaml_quote(x["kind"]))
        out.append("    base_url: " + _yaml_quote(x["base_url"]))
        out.append("    api_key: " + _yaml_quote(x["api_key"]))
        out.append("    enabled: " + str(x["enabled"]).lower())
    out.append("roles:")
    for x in p["roles"]:
        out.append("  - role: " + _yaml_quote(x["role"]))
        out.append("    primary: " + _yaml_quote(x["primary"]))
        out.append("    fallback: " + _yaml_quote(x["fallback"] or ""))
    return "\n".join(out) + "\n"

def import_json(reg, text: str) -> int:
    from .domain import ProviderConfig, RoleRoute
    data = json.loads(text)
    n = 0
    for pd in data.get("providers", []):
        try:
            reg.register_provider(ProviderConfig(
                id=pd["id"], name=pd.get("name", pd["id"]),
                kind=pd.get("kind", "local"),
                base_url=pd.get("base_url", ""),
                api_key=pd.get("api_key", ""),
                enabled=pd.get("enabled", True),
            ))
            n += 1
        except (ValueError, KeyError):
            continue
    reg.discover_models()
    for rd in data.get("roles", []):
        reg.set_role_route(RoleRoute(
            role=rd["role"], primary=rd["primary"],
            fallback=rd.get("fallback") or None,
            params=rd.get("params", {}),
        ))
    return n
