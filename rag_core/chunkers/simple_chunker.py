from ..interfaces import IChunker
from ..models import Document, Chunk
import uuid

class SimpleChunker(IChunker):
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, doc: Document) -> list[Chunk]:
        # 对应UI：生成草稿阶段
        chunks = []
        text = doc.text
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunk_text = text[i:i + self.chunk_size]
            if not chunk_text.strip(): continue
            chunks.append(Chunk(
                chunk_id=str(uuid.uuid4()),
                text=chunk_text,
                metadata={"doc_id": doc.doc_id, "source": doc.metadata.get("source", "")}
            ))
        return chunks
