"""扩展路由（框架无关）"""
from typing import Any, Callable, Dict, List, Tuple

from .config_io import export_json, export_yaml, import_json
from .crud_ext import (
    delete_provider, list_all_models, update_provider, usage_kpi,
)
from .facade import get_facade
from .persistence import save as _save
from .registry import get_registry

Route = Tuple[str, str, Callable[..., Any]]
P = "/api/model-registry"

def _fac():
    f = get_facade()
    f.bootstrap()
    return f

def _update(pid: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    _fac()
    return update_provider(pid, payload)

def _delete(pid: str) -> Dict[str, Any]:
    _fac()
    return delete_provider(pid)

def _models() -> List[Dict[str, Any]]:
    _fac()
    return list_all_models()

def _kpi() -> Dict[str, Any]:
    _fac()
    return usage_kpi()

def _export(fmt: str) -> Dict[str, str]:
    _fac()
    reg = get_registry()
    return {"format": fmt,
            "content": export_yaml(reg) if fmt == "yaml" else export_json(reg)}

def _import(payload: Dict[str, Any]) -> Dict[str, Any]:
    _fac()
    text = payload.get("content", "")
    if not text:
        raise ValueError("empty content")
    reg = get_registry()
    n = import_json(reg, text)
    _save(reg)
    return {"ok": True, "imported": n}

def _verify(pid: str) -> Dict[str, Any]:
    _fac()
    return get_facade().test_and_verify_provider(pid)

def _verified_models() -> List[Dict[str, Any]]:
    _fac()
    return get_facade().verified_models()

def routes() -> List[Route]:
    return [
        ("GET",    P + "/models",             _models),
        ("PATCH",  P + "/providers/{id}",     _update),
        ("DELETE", P + "/providers/{id}",     _delete),
        ("GET",    P + "/kpi/usage",          _kpi),
        ("GET",    P + "/config/export",      lambda: _export("json")),
        ("GET",    P + "/config/export/yaml", lambda: _export("yaml")),
        ("POST",   P + "/config/import",      _import),
        ("POST",   P + "/providers/{id}/verify", _verify),
        ("GET",    P + "/verified-models",    _verified_models),
        ("GET",    P + "/provider-kinds",     lambda: __import__("backend.core.model_registry.provider_kinds", fromlist=["PROVIDER_KINDS"]).PROVIDER_KINDS),
    ]
