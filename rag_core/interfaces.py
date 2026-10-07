from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import Document, Chunk

class IParser(ABC):
    @abstractmethod
    def parse(self, content: bytes, filename: str) -> Document: pass

class IChunker(ABC):
    @abstractmethod
    def chunk(self, doc: Document) -> List[Chunk]: pass

class IEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]: pass

class IVectorStore(ABC):
    @abstractmethod
    def insert(self, chunks: List[Chunk], vectors: List[List[float]]) -> bool: pass
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 3) -> List[Chunk]: pass
