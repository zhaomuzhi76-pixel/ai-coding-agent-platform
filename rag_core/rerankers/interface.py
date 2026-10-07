# 职责：重排序插件契约，避免与原有interfaces.py重复
from abc import ABC, abstractmethod
from typing import List
from ..models import Chunk

class IReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, chunks: List[Chunk]) -> List[Chunk]:
        pass
