# 职责：基于集合/领域的存储插件（对接UI中“已入库数据”面板）
from ..interfaces import IVectorStore
from ..models import Chunk
from typing import List, Tuple, Dict
import math

class PartitionedVectorStore(IVectorStore):
    def __init__(self):
        # 按知识库领域/集合隔离
        self.data: Dict[str, List[Tuple[Chunk, List[float]]]] = {}

    def insert(self, chunks: List[Chunk], vectors: List[List[float]], collection: str = "default") -> bool:
        if collection not in self.data:
            self.data[collection] = []
        for chunk, vec in zip(chunks, vectors):
            self.data[collection].append((chunk, vec))
        return True

    def search(self, query_vector: List[float], top_k: int = 3, collection: str = "default") -> List[Chunk]:
        if collection not in self.data or not self.data[collection]: return []
        scored = []
        for chunk, vec in self.data[collection]:
            dot = sum(a * b for a, b in zip(query_vector, vec))
            norm_a = math.sqrt(sum(a * a for a in query_vector))
            norm_b = math.sqrt(sum(b * b for b in vec))
            score = dot / (norm_a * norm_b + 1e-8)
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def delete(self, collection: str, chunk_ids: List[str]) -> int:
        if collection not in self.data: return 0
        original_len = len(self.data[collection])
        self.data[collection] = [item for item in self.data[collection] if item[0].chunk_id not in chunk_ids]
        return original_len - len(self.data[collection])

    def get_stats(self, collection: str) -> Dict[str, int]:
        docs = len(self.data.get(collection, []))
        return {"doc_count": docs, "chunk_count": docs}
