from __future__ import annotations

from pathlib import Path

from backend.code_intelligence.pipeline.source_reader import (
    SourceReader,
)

from backend.code_intelligence.pipeline.ast_chunk_builder import (
    ASTChunkBuilder,
)

class CodeChunker:
    """
    Build semantic code chunks.

    Responsibility:
        - coordinate source loading
        - build semantic chunks

    Not Responsible:
        - indexing
        - embedding
        - persistence
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "code_semantic_chunking"
    )

    def __init__(
        self,
        reader: SourceReader,
        builder: ASTChunkBuilder,
    ) -> None:

        self.reader = reader
        self.builder = builder

    def chunk(
        self,
        path: Path,
    ) -> list[dict]:

        source = self.reader.read(
            path
        )

        return self.builder.build(
            path,
            source,
        )

    def ready(
        self,
    ) -> bool:

        return (
            self.reader is not None
            and self.builder is not None
        )

__all__ = [
    "CodeChunker",
]
