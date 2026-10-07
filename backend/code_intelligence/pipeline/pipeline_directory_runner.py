from __future__ import annotations

from backend.code_intelligence.index.indexer import (
    CodeIndexer,
)

from backend.code_intelligence.pipeline.pipeline_file_processor import (
    PipelineFileProcessor,
)

class PipelineDirectoryRunner:
    """
    Execute project indexing pipeline.

    Responsibility:
        - iterate indexed files
        - execute file processor
        - aggregate results

    Not Responsible:
        - indexing implementation
        - parsing
        - embedding
        - persistence
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "code_intelligence_pipeline_runner"
    )

    def __init__(
        self,
        indexer: CodeIndexer,
        processor: PipelineFileProcessor,
    ) -> None:

        self.indexer = indexer
        self.processor = processor

    async def run(
        self,
        project: str,
    ) -> dict:

        files = self.indexer.scan_files()

        results = []
        chunks = 0
        vectors = 0

        for file in files:
            result = await self.processor.process(
                project,
                file,
            )

            results.append(
                result
            )

            chunks += result["chunks"]
            vectors += result["vectors"]

        return {
            "files": len(files),
            "chunks": chunks,
            "vectors": vectors,
            "results": results,
        }

    def ready(
        self,
    ) -> bool:

        return (
            self.indexer is not None
            and self.processor is not None
        )

    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "PipelineDirectoryRunner",
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "ready":
                self.ready(),
        }

__all__ = [
    "PipelineDirectoryRunner",
]
