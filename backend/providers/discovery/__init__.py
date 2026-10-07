"""Provider 模型自动发现包。

工业级契约：
  - Ollama 通过 /api/tags 动态发现所有模型
  - 自动识别 chat / embedding / reranker
  - 发现结果合并到 LLMConfig，yaml 无需写死模型清单
"""
from .bootstrap import (
    refresh_ollama_discovery,
    get_discovered,
    get_all_discovered,
    is_ready,
)
from .merger import merge_into_config

__all__ = [
    "refresh_ollama_discovery",
    "get_discovered",
    "get_all_discovered",
    "is_ready",
    "merge_into_config",
]
