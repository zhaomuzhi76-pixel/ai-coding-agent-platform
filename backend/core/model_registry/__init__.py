"""工业级模型注册中心（对外唯一入口）"""
from .domain import ModelInfo, ProviderConfig, RoleRoute
from .registry import ModelRegistry, get_registry, reset_registry
from .bootstrap import bootstrap_default
from .persistence import load as load_store, save as save_store
from .facade import RegistryFacade, get_facade
from .api_routes import routes as api_routes

__all__ = [
    "ModelInfo", "ProviderConfig", "RoleRoute",
    "ModelRegistry", "get_registry", "reset_registry",
    "bootstrap_default", "load_store", "save_store",
    "RegistryFacade", "get_facade", "api_routes",
]
