"""从环境变量引导注册中心（无硬编码）"""
import os

from .domain import ProviderConfig, RoleRoute
from .registry import get_registry

DEFAULT_ROLE_MODELS = {
    "intent": "qwen2.5-coder:7b",
    "plan": "qwen2.5-coder:7b",
    "code": "qwen2.5-coder:7b",
    "review": "qwen2.5-coder:7b",
    "complex": "qwen2.5-coder:7b",
}


def _env(k: str, d: str = "") -> str:
    return os.environ.get(k, d)


def bootstrap_default() -> None:
    reg = get_registry()
    if reg.providers:
        return
    reg.register_provider(ProviderConfig(
        id=_env("BIANCHENG_OLLAMA_ID", "ollama-local"),
        name="本地 Ollama",
        kind="local",
        base_url=_env("BIANCHENG_OLLAMA_URL", "http://127.0.0.1:11434"),
    ))
    if _env("DASHSCOPE_API_KEY"):
        reg.register_provider(ProviderConfig(
            id=_env("BIANCHENG_DASHSCOPE_ID", "dashscope-qwen"),
            name="阿里云百炼",
            kind="cloud",
            base_url=_env("BIANCHENG_DASHSCOPE_URL",
                          "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key=_env("DASHSCOPE_API_KEY"),
        ))
    reg.discover_models()
    for role, mid in DEFAULT_ROLE_MODELS.items():
        reg.set_role_route(RoleRoute(role=role, primary=mid))
