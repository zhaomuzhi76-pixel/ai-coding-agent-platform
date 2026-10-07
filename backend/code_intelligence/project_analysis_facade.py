from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.code_intelligence.context_builder import (
    CodeContextBuilder,
)
from backend.code_intelligence.graph_provider import (
    GraphProvider,
)
from backend.code_intelligence.impact_analyzer import (
    ImpactAnalyzer,
)
from backend.code_intelligence.index.index_service import (
    CodeIndexService,
)

class ProjectAnalysisFacade:
    """
    Industrial project analysis facade.

    Responsibility:
        - coordinate project intelligence services
        - expose project analysis capability

    Not Responsible:
        - source parsing
        - code understanding
        - file analysis
        - indexing implementation
        - graph construction
        - modification
    """

    VERSION = "6.1"

    RESPONSIBILITY = (
        "industrial_project_analysis_facade"
    )

    def __init__(
        self,
        root_path: str,
        index_service: CodeIndexService,
        context_builder: CodeContextBuilder,
        impact_analyzer: ImpactAnalyzer,
        graph_provider: GraphProvider,
    ) -> None:
        self.root_path = Path(root_path)

        if index_service is None:
            raise ValueError("index service required")
        if context_builder is None:
            raise ValueError("context builder required")
        if impact_analyzer is None:
            raise ValueError("impact analyzer required")
        if graph_provider is None:
            raise ValueError("graph provider required")

        self.index_service = index_service
        self.context_builder = context_builder
        self.impact_analyzer = impact_analyzer
        self.graph_provider = graph_provider

        self.analysis_count = 0

    def analyze_project(self) -> dict[str, Any]:
        self.analysis_count += 1
        files = self.index_service.build()

        return {
            "files": files,
            "count": len(files),
        }

    def build_context(
        self,
        *,
        task: str,
        files: list[dict[str, Any]] | None = None,
        impact: dict[str, Any] | None = None,
        memory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.context_builder.build(
            task=task,
            files=files,
            impact=impact,
            memory=memory,
        )

    def analyze_impact(
        self,
        *,
        file: str,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        files = self.index_service.build()

        self.graph_provider.build(
            files
        )

        return self.impact_analyzer.analyze(
            file=file,
            symbol=symbol,
            graph=self.graph_provider,
        )

    def ready(self) -> bool:
        return all(
            (
                self.root_path.exists(),
                self.index_service.ready(),
                self.context_builder.ready(),
                self.impact_analyzer.ready(),
                self.graph_provider.ready(),
            )
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "root_path": str(
                self.root_path
            ),
            "metrics": {
                "analysis": self.analysis_count,
            },
            "components": {
                "index": type(
                    self.index_service
                ).__name__,
                "context": type(
                    self.context_builder
                ).__name__,
                "impact": type(
                    self.impact_analyzer
                ).__name__,
                "graph": type(
                    self.graph_provider
                ).__name__,
            },
            "capabilities": [
                "project_analysis",
                "context_building",
                "impact_analysis",
            ],
        }

__all__ = [
    "ProjectAnalysisFacade",
]
