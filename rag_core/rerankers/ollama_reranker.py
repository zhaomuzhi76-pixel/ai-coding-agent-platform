# 职责：对接 Ollama 本地重排序模型插件
import urllib.request, json
from .interface import IReranker
from ..models import Chunk
from typing import List

class OllamaReranker(IReranker):
    def __init__(self, model_name: str = "dengcao/Qwen3-Reranker-4B:Q5_K_M"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/generate"

    def rerank(self, query: str, chunks: List[Chunk]) -> List[Chunk]:
        scored_chunks = []
        for chunk in chunks:
            prompt = f"Query: {query}\nDocument: {chunk.text}\nRate the relevance (0-10):"
            payload = {"model": self.model_name, "prompt": prompt, "stream": False}
            req = urllib.request.Request(self.url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=5) as res:
                    score = float(json.loads(res.read().decode('utf-8'))["response"].strip()[:3])
                    scored_chunks.append((score, chunk))
            except Exception:
                scored_chunks.append((0.0, chunk))
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_chunks]
