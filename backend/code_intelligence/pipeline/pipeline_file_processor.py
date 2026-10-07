from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.code_intelligence.pipeline.code_chunker import (
    CodeChunker,
)
from backend.code_intelligence.pipeline.embedding_service import (
    EmbeddingService,
)

class PipelineFileProcessor:
    """
    Process one source file in the indexing pipeline.

    Responsibility:
        - coordinate chunk generation
        - convert chunk content to embeddings

    Not Responsible:
        - file discovery
        - parsing
        - vector persistence
    """

    VERSION = "1.1"

    RESPONSIBILITY = (
        "code_pipeline_file_processing"
    )

    def __init__(
        self,
        chunker: CodeChunker,
        embedding: EmbeddingService,
    ) -> None:
        self.chunker = chunker
        self.embedding = embedding

    async def process(
        self,
        project: str,
        file: str,
    ) -> dict[str, Any]:
        path = Path(project) / file
        chunks = self.chunker.chunk(path)

        if chunks:
            texts = [
                self._chunk_content(chunk)
                for chunk in chunks
            ]
            vectors = await self.embedding.embed_batch(
                texts
            )
        else:
            vectors = []

        return {
            "file": file,
            "chunks": len(chunks),
            "vectors": len(vectors),
            "items": chunks,
        }

    def ready(self) -> bool:
        return (
            self.chunker is not None
            and self.embedding is not None
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }

    @staticmethod
    def _chunk_content(
        chunk: dict[str, Any],
    ) -> str:
        content = chunk.get("content")

        if not isinstance(content, str):
            raise TypeError(
                "semantic chunk content must be str"
            )

        if not content:
            raise ValueError(
                "semantic chunk content must not be empty"
            )

        return content

__all__ = [
    "PipelineFileProcessor",
]
