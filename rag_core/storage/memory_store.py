from ..interfaces import IVectorStore
from ..models import Chunk
from typing import List, Tuple
import math

class MemoryVectorStore(IVectorStore):
    def __init__(self):
        self.data: List[Tuple[Chunk, List[float]]] = []

    def insert(self, chunks: List[Chunk], vectors: List[List[float]]) -> bool:
        for chunk, vec in zip(chunks, vectors):
            self.data.append((chunk, vec))
        return True

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Chunk]:
        # 工业级简易余弦相似度计算，满足“召回测试”面板
        scored = []
        for chunk, vec in self.data:
            dot = sum(a * b for a, b in zip(query_vector, vec))
            norm_a = math.sqrt(sum(a * a for a in query_vector))
            norm_b = math.sqrt(sum(b * b for b in vec))
            score = dot / (norm_a * norm_b + 1e-8)
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]
