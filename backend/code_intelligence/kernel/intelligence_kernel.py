from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.code_intelligence.analysis.analyzer import (
    CodeAnalyzer,
)

from backend.code_intelligence.graph_provider import (
    GraphProvider,
)

from backend.code_intelligence.index.index_service import (
    CodeIndexService,
)

class IntelligenceKernel:
    """
    Industrial code intelligence kernel.

    Responsibility:
        - coordinate project intelligence
        - provide unified project understanding
        - provide planner context

    Not Responsible:
        - source parsing
        - indexing implementation
        - modification
        - persistence
    """

    VERSION = "5.0"

    RESPONSIBILITY = (
        "industrial_code_intelligence_kernel",
    )

    def __init__(
        self,
        workspace: str,
        index_service: CodeIndexService,
        analyzer: CodeAnalyzer,
        graph_provider: GraphProvider,
    ) -> None:

        self.workspace = Path(
            workspace
        )

        self.index_service = index_service

        if analyzer is None:
            raise ValueError("analyzer required")
        if graph_provider is None:
            raise ValueError("graph provider required")

        self.analyzer = analyzer
        self.graph = graph_provider

    def scan_project(
        self,
    ) -> list[str]:

        return self.index_service.scan()

    def build_index(
        self,
    ) -> list[dict[str, Any]]:

        return self.index_service.build()

    def analyze_file(
        self,
        path: str,
    ) -> dict[str, Any]:

        target = (
            self.workspace
            /
            path
        )

        if not target.exists():
            raise FileNotFoundError(
                path
            )

        source = target.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        model = self.analyzer.analyze(
            path,
            source,
        )

        return model.dump()

    def project_summary(
        self,
    ) -> dict[str, Any]:

        index = self.build_index()

        return {
            "workspace": str(
                self.workspace
            ),
            "files": len(
                index
            ),
            "graph_ready":
                self.graph.ready(),
            "index_ready":
                self.index_service.ready(),
            "analysis_ready":
                self.analyzer.ready(),
        }

    def project_intelligence(
        self,
    ) -> dict[str, Any]:

        index = self.build_index()

        files = [
            item.get(
                "path",
                "",
            )
            for item in index
        ]

        files = [
            item
            for item in files
            if item
        ]

        return {
            "workspace": str(
                self.workspace
            ),
            "file_count": len(
                files
            ),
            "files": files,
            "summary": self.project_summary(),
            "capabilities": [
                "read_code",
                "search_code",
                "analyze_code",
                "modify_code",
                "verify_code",
            ],
            "components": {
                "index":
                    type(
                        self.index_service
                    ).__name__,
                "analysis":
                    type(
                        self.analyzer
                    ).__name__,
                "graph":
                    type(
                        self.graph
                    ).__name__,
            },
        }

    def ready(
        self,
    ) -> bool:

        return (
            self.workspace.exists()
            and self.index_service.ready()
            and self.analyzer.ready()
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "IntelligenceKernel",
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "workspace":
                str(
                    self.workspace
                ),
            "ready":
                self.ready(),
            "components": {
                "index":
                    type(
                        self.index_service
                    ).__name__,
                "analysis":
                    type(
                        self.analyzer
                    ).__name__,
                "graph":
                    type(
                        self.graph
                    ).__name__,
            },
        }

__all__ = [
    "IntelligenceKernel",
]
