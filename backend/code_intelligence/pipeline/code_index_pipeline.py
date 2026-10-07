from __future__ import annotations

from typing import Any

from backend.code_intelligence.pipeline.pipeline_directory_runner import (
    PipelineDirectoryRunner,
)

class CodeIndexPipeline:
    """
    Code indexing workflow coordinator.

    Responsibility:
        - coordinate indexing workflow

    Not Responsible:
        - scanner creation
        - chunk creation
        - embedding creation
        - storage
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "code_index_pipeline_coordination"
    )

    def __init__(
        self,
        runner: PipelineDirectoryRunner,
    ) -> None:

        self.runner = runner

    async def index_project(
        self,
        project: str,
    ) -> dict[str, Any]:

        return await self.runner.run(
            project
        )

    def ready(
        self,
    ) -> bool:

        return self.runner is not None

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "CodeIndexPipeline",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }

__all__ = [
    "CodeIndexPipeline",
]
