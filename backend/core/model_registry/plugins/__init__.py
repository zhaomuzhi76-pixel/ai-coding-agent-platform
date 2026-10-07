"""Provider 插件注册表（开闭原则：新增 Provider 只需新增文件并注册）"""
from typing import Dict, Optional, Type

from .base import BaseProviderPlugin
from .ollama_plugin import OllamaLocalPlugin
from .dashscope_plugin import DashScopePlugin
from .openai_compatible_plugin import OpenAICompatiblePlugin

PLUGIN_REGISTRY: Dict[str, Type[BaseProviderPlugin]] = {
    # 本地
    "ollama":       OllamaLocalPlugin,
    "local":        OllamaLocalPlugin,
    "ollama-local": OllamaLocalPlugin,
    "vllm":         OpenAICompatiblePlugin,
    "lmstudio":     OpenAICompatiblePlugin,
    # 云端（默认 OpenAI 兼容）
    "openai":       OpenAICompatiblePlugin,
    "anthropic":    OpenAICompatiblePlugin,
    "deepseek":     OpenAICompatiblePlugin,
    "zhipu":        OpenAICompatiblePlugin,
    "moonshot":     OpenAICompatiblePlugin,
    "gemini":       OpenAICompatiblePlugin,
    "siliconflow":  OpenAICompatiblePlugin,
    "openrouter":   OpenAICompatiblePlugin,
    "custom":       OpenAICompatiblePlugin,
    # 阿里云百炼：特殊 DashScope 端点优先
    "dashscope":    DashScopePlugin,
    "cloud":        DashScopePlugin,
    "dashscope-qwen": DashScopePlugin,
}


def get_plugin_class(kind: str) -> Optional[Type[BaseProviderPlugin]]:
    return PLUGIN_REGISTRY.get(kind)


__all__ = ["BaseProviderPlugin", "OllamaLocalPlugin", "DashScopePlugin",
           "OpenAICompatiblePlugin", "PLUGIN_REGISTRY", "get_plugin_class"]
