"""注册中心持久化：JSON 单文件存储，原子写入（无重复职责）"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from .domain import ModelInfo, ProviderConfig, RoleRoute

DEFAULT_STORE = Path(
    os.environ.get(
        "BIANCHENG_MODEL_STORE",
        Path.home() / ".biancheng" / "model_registry.json",
    )
)


def _dump_provider(p: ProviderConfig) -> Dict[str, Any]:
    return {
        "id": p.id, "name": p.name, "kind": p.kind,
        "base_url": p.base_url, "api_key": p.api_key,
        "enabled": p.enabled,
    }


def _load_provider(d: Dict[str, Any]) -> ProviderConfig:
    return ProviderConfig(
        id=d["id"], name=d.get("name", d["id"]),
        kind=d.get("kind", "local"), base_url=d.get("base_url", ""),
        api_key=d.get("api_key", ""), enabled=d.get("enabled", True),
    )


def _dump_route(r: RoleRoute) -> Dict[str, Any]:
    return {"role": r.role, "primary": r.primary,
            "fallback": r.fallback, "params": r.params}


def _load_route(d: Dict[str, Any]) -> RoleRoute:
    return RoleRoute(role=d["role"], primary=d["primary"],
                     fallback=d.get("fallback"), params=d.get("params", {}))


def save(registry, path: Path = None) -> Path:
    target = path or DEFAULT_STORE
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "providers": [_dump_provider(p) for p in registry.providers.values()],
        "roles": [_dump_route(r) for r in registry.roles.values()],
        "verification": registry.verification.export(),
    }
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return target


def load(registry, path: Path = None) -> bool:
    target = path or DEFAULT_STORE
    if not target.exists():
        return False
    data = json.loads(target.read_text(encoding="utf-8"))
    for pd in data.get("providers", []):
        try:
            registry.register_provider(_load_provider(pd))
        except ValueError:
            continue
    registry.discover_models()
    for rd in data.get("roles", []):
        registry.set_role_route(_load_route(rd))
    if "verification" in data:
        registry.verification.load(data["verification"])
    return True
