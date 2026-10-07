"""模型注册中心 - 领域模型（单一职责：只定义数据结构）"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ProviderConfig:
    id: str
    name: str
    kind: str  # "local" | "cloud"
    base_url: str
    api_key: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class ModelInfo:
    id: str
    provider_id: str
    display_name: str = ""
    context_window: int = 8192
    cost_per_1k: float = 0.0
    tags: tuple = ()


@dataclass
class RoleRoute:
    role: str
    primary: str
    fallback: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
