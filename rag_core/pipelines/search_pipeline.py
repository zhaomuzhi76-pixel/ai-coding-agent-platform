# 职责：检索流水线（包含重排序节点），对接UI“召回测试”
from typing import List
from ..models import Chunk
from ..interfaces import IEmbedder, IVectorStore
from ..rerankers.interface import IReranker

class SearchPipeline:
    def __init__(self, embedder: IEmbedder, store: IVectorStore, reranker: IReranker = None):
        self.embedder = embedder
        self.store = store
        self.reranker = reranker

    def search(self, query: str, top_k: int = 3, collection: str = "default", enable_rerank: bool = False) -> List[Chunk]:
        query_vector = self.embedder.embed([query])[0]
        # 召回扩大范围，为重排序准备
        chunks = self.store.search(query_vector, top_k * 2, collection)
        if enable_rerank and self.reranker and chunks:
            chunks = self.reranker.rerank(query, chunks)
        return chunks[:top_k]
