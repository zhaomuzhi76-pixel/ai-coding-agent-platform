"""角色扩展 API：成本预估 + 角色级测试"""
from typing import Any, Callable, Dict, List, Tuple

from .cost_estimate import estimate
from .facade import get_facade
from .registry import get_registry
from .role_test import test_role

P = "/api/model-registry"


def _fac():
    f = get_facade()
    f.bootstrap()
    return f


def _cost() -> Dict[str, Any]:
    _fac()
    return estimate(get_registry())


async def _test(role: str) -> Dict[str, Any]:
    _fac()
    return await test_role(role)


def routes() -> List[Tuple[str, str, Callable[..., Any]]]:
    return [
        ("GET",  P + "/cost-estimate",        _cost),
        ("POST", P + "/roles/{role}/test",    _test),
    ]
