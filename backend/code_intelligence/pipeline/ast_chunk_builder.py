from __future__ import annotations

import ast
from pathlib import Path

from backend.code_intelligence.analysis.python_analyzer import (
    PythonAnalyzer,
)

class ASTChunkBuilder:
    """
    Build semantic chunks from Python AST.

    Responsibility:
        - transform AST nodes into semantic chunks

    Not Responsible:
        - source loading
        - indexing
        - embedding
        - persistence
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "ast_semantic_chunk_builder"
    )

    def __init__(
        self,
        analyzer: PythonAnalyzer,
    ) -> None:

        self.analyzer = analyzer

    def build(
        self,
        path: Path,
        source: str,
    ) -> list[dict]:

        tree = self.analyzer.parse(
            source
        )

        chunks = []

        for node in tree.body:

            if isinstance(
                node,
                ast.ClassDef,
            ):

                chunks.append(
                    self._make(
                        "class",
                        node.name,
                        path,
                        node,
                        source,
                    )
                )

                chunks.extend(
                    self._methods(
                        node,
                        path,
                        source,
                    )
                )

            elif isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                chunks.append(
                    self._make(
                        "function",
                        node.name,
                        path,
                        node,
                        source,
                    )
                )

        return chunks

    def _methods(
        self,
        node: ast.ClassDef,
        path: Path,
        source: str,
    ) -> list[dict]:

        chunks = []

        for child in node.body:

            if isinstance(
                child,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                chunks.append(
                    self._make(
                        "method",
                        f"{node.name}.{child.name}",
                        path,
                        child,
                        source,
                    )
                )

        return chunks

    def _make(
        self,
        kind: str,
        name: str,
        path: Path,
        node: ast.AST,
        source: str,
    ) -> dict:

        return {
            "type":
                kind,

            "name":
                name,

            "file":
                str(path),

            "start_line":
                node.lineno,

            "end_line":
                node.end_lineno,

            "content":
                self._extract(
                    source,
                    node,
                ),
        }

    def _extract(
        self,
        source: str,
        node: ast.AST,
    ) -> str:

        lines = source.splitlines()

        return "\n".join(
            lines[
                node.lineno - 1:
                node.end_lineno
            ]
        )

    def ready(
        self,
    ) -> bool:

        return self.analyzer is not None

    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "ASTChunkBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }

__all__ = [
    "ASTChunkBuilder",
]
