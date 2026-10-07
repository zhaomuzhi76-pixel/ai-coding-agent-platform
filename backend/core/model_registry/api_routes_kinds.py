"""Provider 类型清单端点（供前端下拉分组显示）"""
from typing import Any, Dict, List, Tuple

from .provider_kinds import PROVIDER_KINDS

P = "/api/model-registry"


def list_kinds() -> List[Dict[str, Any]]:
    return PROVIDER_KINDS


def routes():
    return [("GET", P + "/provider-kinds", list_kinds)]
