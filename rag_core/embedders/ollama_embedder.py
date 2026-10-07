# 职责：对接 Ollama 本地向量模型插件
import urllib.request, json
from ..interfaces import IEmbedder
from typing import List

class OllamaEmbedder(IEmbedder):
    def __init__(self, model_name: str = "qwen3-embedding:8b"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/embeddings"

    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors = []
        for text in texts:
            payload = {"model": self.model_name, "prompt": text}
            req = urllib.request.Request(self.url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=5) as res:
                    vectors.append(json.loads(res.read().decode('utf-8'))["embedding"])
            except Exception:
                vectors.append([0.0] * 128) # 异常兜底
        return vectors
