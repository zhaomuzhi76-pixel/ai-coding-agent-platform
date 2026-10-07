from __future__ import annotations

from typing import Any

from backend.code_intelligence.analysis.model import (
    ClassModel,
    CodeFileModel,
    FunctionModel,
    ImportModel,
)

from backend.code_intelligence.analysis.python_analyzer import (
    PythonAnalyzer,
)
from backend.core.code_intelligence.analysis_port import (
    CodeAnalyzerProtocol,
)

class CodeAnalyzer(CodeAnalyzerProtocol):
    """
    Industrial code analysis facade.

    Responsibility:
        - coordinate source analysis
        - build code knowledge model

    Not Responsible:
        - file loading
        - indexing
        - storage
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "industrial_code_analysis_facade"
    )

    def __init__(
        self,
        analyzer: PythonAnalyzer | None = None,
    ) -> None:

        self.analyzer = (
            analyzer
            or PythonAnalyzer()
        )

    def analyze(
        self,
        path: str,
        source: str,
    ) -> CodeFileModel:

        result = self.analyzer.analyze(
            source
        )

        return CodeFileModel(
            path=path,
            language=result["language"],
            lines=result["lines"],
            classes=[
                ClassModel(
                    name=name
                )
                for name in result["classes"]
            ],
            functions=[
                FunctionModel(
                    name=name
                )
                for name in result["functions"]
            ],
            imports=[
                ImportModel(
                    module=name
                )
                for name in result["imports"]
            ],
        )

    def ready(
        self,
    ) -> bool:

        return self.analyzer.ready()

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "CodeAnalyzer",
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "ready":
                self.ready(),
        }

__all__ = [
    "CodeAnalyzer",
]
