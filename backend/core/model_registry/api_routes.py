"""HTTP 路由适配层（框架无关：返回 (method, path, handler) 三元组）

挂到 FastAPI / Flask / aiohttp 均可，本文件不 import web 框架。
"""
from typing import Any, Callable, Dict, List, Tuple

from .domain import ProviderConfig
from .facade import get_facade

Route = Tuple[str, str, Callable[..., Any]]


def _facade():
    f = get_facade()
    f.bootstrap()
    return f


def list_providers() -> List[Dict[str, Any]]:
    return _facade().provider_cards()


def list_models(provider_id: str) -> List[Dict[str, Any]]:
    return _facade().models_of(provider_id)


def list_roles() -> List[Dict[str, Any]]:
    return _facade().role_cards()


def get_kpi() -> Dict[str, Any]:
    return _facade().kpi()


def test_provider(provider_id: str) -> Dict[str, Any]:
    return {"provider": provider_id,
            "connected": _facade().test_provider(provider_id)}

def verify_provider(provider_id: str) -> Dict[str, Any]:
    """[VERIFY] 测试 + 把通过的模型写入 verified 集合（持久化）。"""
    return _facade().test_and_verify_provider(provider_id)



def create_provider(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = ProviderConfig(
        id=payload["id"], name=payload.get("name", payload["id"]),
        kind=payload.get("kind", "local"),
        base_url=payload.get("base_url", ""),
        api_key=payload.get("api_key", ""),
        enabled=payload.get("enabled", True),
    )
    _facade().upsert_provider(cfg)
    return {"ok": True, "id": cfg.id}


def bind_role(payload: Dict[str, Any]) -> Dict[str, Any]:
    _facade().set_role(
        payload["role"], payload["primary"], payload.get("fallback")
    )
    return {"ok": True, "role": payload["role"]}


def routes() -> List[Route]:
    return [
        ("GET",  "/api/model-registry/providers",        list_providers),
        ("POST", "/api/model-registry/providers",        create_provider),
        ("GET",  "/api/model-registry/providers/{id}/models", list_models),
        ("POST", "/api/model-registry/providers/{id}/test",   test_provider),
        ("POST", "/api/model-registry/providers/{id}/verify", verify_provider),
        ("GET",  "/api/model-registry/roles",            list_roles),
        ("POST", "/api/model-registry/roles",            bind_role),
        ("GET",  "/api/model-registry/kpi",              get_kpi),
    ]
