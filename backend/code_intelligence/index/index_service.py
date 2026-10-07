from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.code_intelligence.analysis.analyzer import (
    CodeAnalyzer,
)
from backend.code_intelligence.index.indexer import (
    CodeIndexer,
)

class CodeIndexService:
    """
    Industrial code indexing and source-structure service.

    Owns:
        - repository file discovery
        - normalized source inventory
        - symbol/import extraction for index consumers

    Does not own:
        - graph traversal
        - embedding
        - persistence
    """

    VERSION = "3.0"

    def __init__(
        self,
        workspace: str,
        indexer: CodeIndexer | None = None,
        analyzer: CodeAnalyzer | None = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.indexer = (
            indexer
            or CodeIndexer(str(self.workspace))
        )
        self.analyzer = (
            analyzer
            or CodeAnalyzer()
        )
        self.build_count = 0

    def scan(self) -> list[str]:
        return self.indexer.scan_files()

    def build(self) -> list[dict[str, Any]]:
        if not self.ready():
            raise RuntimeError(
                "code index service unavailable"
            )

        result: list[dict[str, Any]] = []

        for path in self.scan():
            item: dict[str, Any] = {
                "path": path,
                "symbols": [],
                "imports": [],
            }

            source_path = self.workspace / path

            try:
                source = source_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
                model = self.analyzer.analyze(
                    path,
                    source,
                ).dump()

                item["symbols"] = (
                    list(model["classes"])
                    + list(model["functions"])
                )
                item["imports"] = list(
                    model["imports"]
                )
            except (
                OSError,
                UnicodeError,
                SyntaxError,
            ):
                pass

            result.append(item)

        self.build_count += 1
        return result

    def ready(self) -> bool:
        return (
            self.workspace.exists()
            and self.indexer.ready()
            and self.analyzer.ready()
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "workspace": str(self.workspace),
            "component": type(
                self.indexer
            ).__name__,
            "analyzer": type(
                self.analyzer
            ).__name__,
            "build_count": self.build_count,
        }

__all__ = [
    "CodeIndexService",
]
