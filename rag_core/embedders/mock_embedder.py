from ..interfaces import IEmbedder
from typing import List

class MockEmbedder(IEmbedder):
    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, texts: List[str]) -> List[List[float]]:
        # 工业级测试替身：不依赖外部API，极速响应
        return [[float(len(t) % 10) / 10.0] * self.dim for t in texts]
