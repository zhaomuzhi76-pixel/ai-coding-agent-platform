from __future__ import annotations

import ast

from typing import Any

class PythonAnalyzer:
    """
    Industrial Python source analyzer.

    Responsibility:
        - parse python source
        - extract source structure

    Not Responsible:
        - file access
        - indexing
        - persistence
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "industrial_python_source_analysis"
    )

    def parse(
        self,
        source: str,
    ) -> ast.AST:

        return ast.parse(
            source
        )

    def analyze(
        self,
        source: str,
    ) -> dict[str, Any]:

        tree = self.parse(
            source
        )

        return {
            "language": "python",
            "lines": len(
                source.splitlines()
            ),
            "classes": self.classes(
                tree
            ),
            "functions": self.functions(
                tree
            ),
            "imports": self.imports(
                tree
            ),
        }

    def classes(
        self,
        tree: ast.AST,
    ) -> list[str]:

        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(
                node,
                ast.ClassDef,
            )
        ]

    def functions(
        self,
        tree: ast.AST,
    ) -> list[str]:

        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
        ]

    def imports(
        self,
        tree: ast.AST,
    ) -> list[str]:

        result = []

        for node in ast.walk(tree):

            if isinstance(
                node,
                ast.Import,
            ):
                result.extend(
                    item.name
                    for item in node.names
                )

            if isinstance(
                node,
                ast.ImportFrom,
            ):
                if node.module:
                    result.append(
                        node.module
                    )

        return sorted(
            set(result)
        )

    def ready(
        self,
    ) -> bool:

        return True

__all__ = [
    "PythonAnalyzer",
]
