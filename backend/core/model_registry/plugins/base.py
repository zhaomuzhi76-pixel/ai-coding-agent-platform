"""Provider 插件基类 - 所有 Provider 必须实现此契约"""
from abc import ABC, abstractmethod
from typing import List

from ..domain import ModelInfo, ProviderConfig


class BaseProviderPlugin(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def test_connection(self) -> bool: ...

    @abstractmethod
    def fetch_models(self) -> List[ModelInfo]: ...

    @abstractmethod
    def generate(self, model_id: str, prompt: str, **kwargs) -> str: ...
